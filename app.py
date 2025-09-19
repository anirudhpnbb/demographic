"""
Patient Demographic and Health Management System
Simplified version using basic Python libraries and built-in HTTP server
"""

import http.server
import socketserver
import json
import sqlite3
import urllib.parse
from datetime import datetime, date
import os
import base64
from io import BytesIO

# Database setup
DATABASE = 'demographic.db'

def init_database():
    """Initialize the SQLite database with tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth DATE NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            address TEXT,
            emergency_contact TEXT,
            location_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            location_id INTEGER NOT NULL,
            height REAL,
            weight REAL,
            temperature REAL,
            blood_pressure_systolic INTEGER,
            blood_pressure_diastolic INTEGER,
            heart_rate INTEGER,
            notes TEXT,
            recorded_by TEXT NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (location_id) REFERENCES locations (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blood_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id TEXT UNIQUE NOT NULL,
            patient_id INTEGER NOT NULL,
            collection_location_id INTEGER NOT NULL,
            test_location_id INTEGER,
            collected_by TEXT NOT NULL,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            test_type TEXT NOT NULL,
            status TEXT DEFAULT 'collected',
            results TEXT,
            tested_by TEXT,
            tested_at TIMESTAMP,
            results_sent_at TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (collection_location_id) REFERENCES locations (id),
            FOREIGN KEY (test_location_id) REFERENCES locations (id)
        )
    ''')
    
    # Insert default location if none exists
    cursor.execute('SELECT COUNT(*) FROM locations')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO locations (name, address, phone)
            VALUES ('Main Hospital', '123 Healthcare Street, Medical City', '+1234567890')
        ''')
    
    conn.commit()
    conn.close()

def generate_patient_id():
    """Generate unique patient ID"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM patients')
    count = cursor.fetchone()[0]
    conn.close()
    return f"PAT{(count + 1):06d}"

def generate_sample_id():
    """Generate unique sample ID"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM blood_samples')
    count = cursor.fetchone()[0]
    conn.close()
    return f"BS{(count + 1):06d}"

def generate_qr_code_simple(data):
    """Generate a simple text-based QR representation (placeholder)"""
    return f"QR:{data}"

def simulate_whatsapp_send(phone, message):
    """Simulate WhatsApp message sending"""
    print(f"[WhatsApp Simulation] Sending to {phone}:")
    print(f"Message: {message}")
    return True

class DemographicHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_dashboard()
        elif self.path == '/patients':
            self.send_patients_list()
        elif self.path == '/locations':
            self.send_locations_list()
        elif self.path == '/blood_samples':
            self.send_blood_samples_list()
        elif self.path.startswith('/patient/'):
            patient_id = self.path.split('/')[-1]
            self.send_patient_details(patient_id)
        elif self.path == '/register_patient':
            self.send_register_patient_form()
        elif self.path == '/search_patient':
            self.send_search_patient_form()
        elif self.path == '/add_location':
            self.send_add_location_form()
        elif self.path.startswith('/add_health_record/'):
            patient_id = self.path.split('/')[-1]
            self.send_add_health_record_form(patient_id)
        elif self.path.startswith('/collect_blood_sample/'):
            patient_id = self.path.split('/')[-1]
            self.send_collect_blood_sample_form(patient_id)
        elif self.path.startswith('/update_test_results/'):
            sample_id = self.path.split('/')[-1]
            self.send_update_test_results_form(sample_id)
        elif self.path.startswith('/send_results/'):
            sample_id = self.path.split('/')[-1]
            self.handle_send_results(sample_id)
        else:
            self.send_error(404, "Page not found")
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = urllib.parse.parse_qs(post_data.decode('utf-8'))
        
        if self.path == '/register_patient':
            self.handle_register_patient(data)
        elif self.path == '/search_patient':
            self.handle_search_patient(data)
        elif self.path == '/add_location':
            self.handle_add_location(data)
        elif self.path.startswith('/add_health_record/'):
            patient_id = self.path.split('/')[-1]
            self.handle_add_health_record(patient_id, data)
        elif self.path.startswith('/collect_blood_sample/'):
            patient_id = self.path.split('/')[-1]
            self.handle_collect_blood_sample(patient_id, data)
        elif self.path.startswith('/update_test_results/'):
            sample_id = self.path.split('/')[-1]
            self.handle_update_test_results(sample_id, data)
        else:
            self.send_error(404, "Action not found")
    
    def send_html_response(self, content):
        """Send HTML response"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def send_dashboard(self):
        """Send dashboard page"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM patients')
        total_patients = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM locations')
        total_locations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM blood_samples WHERE status = 'collected'")
        pending_samples = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT p.*, l.name as location_name FROM patients p
            JOIN locations l ON p.location_id = l.id
            ORDER BY p.created_at DESC LIMIT 5
        ''')
        recent_patients = cursor.fetchall()
        
        conn.close()
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Patient Demographic System</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
                .nav {{ background: #f8f9fa; padding: 10px; }}
                .nav a {{ margin-right: 20px; text-decoration: none; color: #007bff; }}
                .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
                .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 5px; flex: 1; text-align: center; }}
                .actions {{ background: white; padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin: 20px 0; }}
                .recent {{ background: white; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .btn {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; display: inline-block; margin: 5px; }}
                .btn:hover {{ background: #0056b3; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Patient Demographic System</h1>
            </div>
            <div class="nav">
                <a href="/">Dashboard</a>
                <a href="/patients">Patients</a>
                <a href="/locations">Locations</a>
                <a href="/blood_samples">Blood Samples</a>
                <a href="/search_patient">Search Patient</a>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>{total_patients}</h3>
                    <p>Total Patients</p>
                </div>
                <div class="stat-card">
                    <h3>{total_locations}</h3>
                    <p>Locations</p>
                </div>
                <div class="stat-card">
                    <h3>{pending_samples}</h3>
                    <p>Pending Tests</p>
                </div>
            </div>
            
            <div class="actions">
                <h3>Quick Actions</h3>
                <a href="/register_patient" class="btn">Register New Patient</a>
                <a href="/search_patient" class="btn">Search Patient</a>
                <a href="/add_location" class="btn">Add Location</a>
            </div>
            
            <div class="recent">
                <h3>Recent Patients</h3>
                {''.join([f'<p><a href="/patient/{p[1]}">{p[2]} {p[3]} ({p[1]})</a> - {p[-1]}</p>' for p in recent_patients]) if recent_patients else '<p>No patients registered yet.</p>'}
            </div>
        </body>
        </html>
        '''
        self.send_html_response(html)
    
    def send_register_patient_form(self):
        """Send patient registration form"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM locations')
        locations = cursor.fetchall()
        conn.close()
        
        location_options = ''.join([f'<option value="{loc[0]}">{loc[1]}</option>' for loc in locations])
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Register Patient</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .form {{ max-width: 600px; margin: 0 auto; }}
                .field {{ margin: 15px 0; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input, select, textarea {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }}
                .btn {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; }}
                .btn:hover {{ background: #0056b3; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ color: #007bff; text-decoration: none; margin-right: 10px; }}
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/">← Back to Dashboard</a>
            </div>
            <div class="form">
                <h2>Register New Patient</h2>
                <form method="POST" action="/register_patient">
                    <div class="field">
                        <label>First Name *</label>
                        <input type="text" name="first_name" required>
                    </div>
                    <div class="field">
                        <label>Last Name *</label>
                        <input type="text" name="last_name" required>
                    </div>
                    <div class="field">
                        <label>Date of Birth *</label>
                        <input type="date" name="date_of_birth" required>
                    </div>
                    <div class="field">
                        <label>Gender *</label>
                        <select name="gender" required>
                            <option value="">Select Gender</option>
                            <option value="Male">Male</option>
                            <option value="Female">Female</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    <div class="field">
                        <label>Phone *</label>
                        <input type="tel" name="phone" required>
                    </div>
                    <div class="field">
                        <label>Email</label>
                        <input type="email" name="email">
                    </div>
                    <div class="field">
                        <label>Address</label>
                        <textarea name="address" rows="3"></textarea>
                    </div>
                    <div class="field">
                        <label>Emergency Contact</label>
                        <input type="tel" name="emergency_contact">
                    </div>
                    <div class="field">
                        <label>Registration Location *</label>
                        <select name="location_id" required>
                            <option value="">Select Location</option>
                            {location_options}
                        </select>
                    </div>
                    <button type="submit" class="btn">Register Patient</button>
                </form>
            </div>
        </body>
        </html>
        '''
        self.send_html_response(html)
    
    def handle_register_patient(self, data):
        """Handle patient registration"""
        try:
            patient_id = generate_patient_id()
            
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO patients 
                (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, emergency_contact, location_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_id,
                data['first_name'][0],
                data['last_name'][0],
                data['date_of_birth'][0],
                data['gender'][0],
                data['phone'][0],
                data.get('email', [''])[0],
                data.get('address', [''])[0],
                data.get('emergency_contact', [''])[0],
                data['location_id'][0]
            ))
            conn.commit()
            conn.close()
            
            # Redirect to patient details
            self.send_response(302)
            self.send_header('Location', f'/patient/{patient_id}')
            self.end_headers()
            
        except Exception as e:
            self.send_error(500, f"Registration failed: {str(e)}")
    
    def send_patient_details(self, patient_id):
        """Send patient details page"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get patient info
        cursor.execute('''
            SELECT p.*, l.name as location_name FROM patients p
            JOIN locations l ON p.location_id = l.id
            WHERE p.patient_id = ?
        ''', (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            self.send_error(404, "Patient not found")
            return
        
        # Get health records
        cursor.execute('''
            SELECT hr.*, l.name as location_name FROM health_records hr
            JOIN locations l ON hr.location_id = l.id
            WHERE hr.patient_id = ?
            ORDER BY hr.recorded_at DESC
        ''', (patient[0],))
        health_records = cursor.fetchall()
        
        # Get blood samples
        cursor.execute('''
            SELECT bs.*, cl.name as collection_location, tl.name as test_location 
            FROM blood_samples bs
            JOIN locations cl ON bs.collection_location_id = cl.id
            LEFT JOIN locations tl ON bs.test_location_id = tl.id
            WHERE bs.patient_id = ?
            ORDER BY bs.collected_at DESC
        ''', (patient[0],))
        blood_samples = cursor.fetchall()
        
        conn.close()
        
        # Generate simple QR code placeholder
        qr_code = generate_qr_code_simple(patient_id)
        
        health_records_html = ''
        if health_records:
            health_records_html = '<h3>Health Records</h3><table border="1" style="width:100%; border-collapse: collapse;">'
            health_records_html += '<tr><th>Date</th><th>Location</th><th>Height</th><th>Weight</th><th>Temperature</th><th>BP</th><th>Heart Rate</th><th>Recorded By</th></tr>'
            for record in health_records:
                bp = f"{record[5]}/{record[6]}" if record[5] and record[6] else "-"
                health_records_html += f'<tr><td>{record[11]}</td><td>{record[-1]}</td><td>{record[3] or "-"}</td><td>{record[4] or "-"}</td><td>{record[5] or "-"}</td><td>{bp}</td><td>{record[7] or "-"}</td><td>{record[9]}</td></tr>'
            health_records_html += '</table>'
        
        blood_samples_html = ''
        if blood_samples:
            blood_samples_html = '<h3>Blood Samples</h3><table border="1" style="width:100%; border-collapse: collapse;">'
            blood_samples_html += '<tr><th>Sample ID</th><th>Test Type</th><th>Status</th><th>Collection Date</th><th>Actions</th></tr>'
            for sample in blood_samples:
                action = ""
                if sample[8] == 'collected':
                    action = f'<a href="/update_test_results/{sample[1]}">Update Results</a>'
                elif sample[8] == 'tested':
                    action = f'<a href="/send_results/{sample[1]}">Send Results</a>'
                blood_samples_html += f'<tr><td>{sample[1]}</td><td>{sample[7]}</td><td>{sample[8]}</td><td>{sample[6]}</td><td>{action}</td></tr>'
            blood_samples_html += '</table>'
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Patient Details - {patient[2]} {patient[3]}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .patient-info {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .actions {{ margin: 20px 0; }}
                .btn {{ background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 3px; margin-right: 10px; }}
                .btn:hover {{ background: #0056b3; }}
                table {{ margin: 20px 0; }}
                th, td {{ padding: 8px; text-align: left; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ color: #007bff; text-decoration: none; margin-right: 10px; }}
                .qr {{ background: #e9ecef; padding: 20px; text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/">← Dashboard</a> | <a href="/patients">Patients</a>
            </div>
            
            <div class="patient-info">
                <h2>Patient Details - {patient[1]}</h2>
                <p><strong>Name:</strong> {patient[2]} {patient[3]}</p>
                <p><strong>Date of Birth:</strong> {patient[4]}</p>
                <p><strong>Gender:</strong> {patient[5]}</p>
                <p><strong>Phone:</strong> {patient[6]}</p>
                <p><strong>Email:</strong> {patient[7] or 'N/A'}</p>
                <p><strong>Address:</strong> {patient[8] or 'N/A'}</p>
                <p><strong>Emergency Contact:</strong> {patient[9] or 'N/A'}</p>
                <p><strong>Registered at:</strong> {patient[-1]}</p>
            </div>
            
            <div class="qr">
                <h4>Patient QR Code</h4>
                <p>{qr_code}</p>
                <small>Use this to quickly access patient information</small>
            </div>
            
            <div class="actions">
                <a href="/add_health_record/{patient[1]}" class="btn">Add Health Record</a>
                <a href="/collect_blood_sample/{patient[1]}" class="btn">Collect Blood Sample</a>
            </div>
            
            {health_records_html}
            {blood_samples_html}
        </body>
        </html>
        '''
        self.send_html_response(html)
    
    def send_patients_list(self):
        """Send patients list page"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, l.name as location_name FROM patients p
            JOIN locations l ON p.location_id = l.id
            ORDER BY p.created_at DESC
        ''')
        patients = cursor.fetchall()
        conn.close()
        
        patients_html = ''
        if patients:
            patients_html = '<table border="1" style="width:100%; border-collapse: collapse;">'
            patients_html += '<tr><th>Patient ID</th><th>Name</th><th>DOB</th><th>Gender</th><th>Phone</th><th>Location</th><th>Actions</th></tr>'
            for patient in patients:
                patients_html += f'<tr><td>{patient[1]}</td><td>{patient[2]} {patient[3]}</td><td>{patient[4]}</td><td>{patient[5]}</td><td>{patient[6]}</td><td>{patient[-1]}</td><td><a href="/patient/{patient[1]}">View</a></td></tr>'
            patients_html += '</table>'
        else:
            patients_html = '<p>No patients registered yet.</p>'
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Patients</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ color: #007bff; text-decoration: none; margin-right: 10px; }}
                .btn {{ background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 3px; }}
                .btn:hover {{ background: #0056b3; }}
                table {{ margin: 20px 0; }}
                th, td {{ padding: 8px; text-align: left; }}
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/">← Dashboard</a>
            </div>
            <h2>Patients</h2>
            <a href="/register_patient" class="btn">Register New Patient</a>
            {patients_html}
        </body>
        </html>
        '''
        self.send_html_response(html)
    
    def send_locations_list(self):
        """Send locations list page"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM locations ORDER BY created_at DESC')
        locations = cursor.fetchall()
        conn.close()
        
        locations_html = ''
        if locations:
            locations_html = '<table border="1" style="width:100%; border-collapse: collapse;">'
            locations_html += '<tr><th>Name</th><th>Address</th><th>Phone</th><th>Created</th></tr>'
            for location in locations:
                locations_html += f'<tr><td>{location[1]}</td><td>{location[2] or "N/A"}</td><td>{location[3] or "N/A"}</td><td>{location[4]}</td></tr>'
            locations_html += '</table>'
        else:
            locations_html = '<p>No locations added yet.</p>'
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Locations</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ color: #007bff; text-decoration: none; margin-right: 10px; }}
                .btn {{ background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 3px; }}
                .btn:hover {{ background: #0056b3; }}
                table {{ margin: 20px 0; }}
                th, td {{ padding: 8px; text-align: left; }}
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/">← Dashboard</a>
            </div>
            <h2>Locations</h2>
            <a href="/add_location" class="btn">Add Location</a>
            {locations_html}
        </body>
        </html>
        '''
        self.send_html_response(html)
    
    def send_blood_samples_list(self):
        """Send blood samples list page"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT bs.*, p.first_name, p.last_name, p.patient_id, cl.name as collection_location 
            FROM blood_samples bs
            JOIN patients p ON bs.patient_id = p.id
            JOIN locations cl ON bs.collection_location_id = cl.id
            ORDER BY bs.collected_at DESC
        ''')
        samples = cursor.fetchall()
        conn.close()
        
        samples_html = ''
        if samples:
            samples_html = '<table border="1" style="width:100%; border-collapse: collapse;">'
            samples_html += '<tr><th>Sample ID</th><th>Patient</th><th>Test Type</th><th>Status</th><th>Collection Date</th><th>Actions</th></tr>'
            for sample in samples:
                action = ""
                if sample[8] == 'collected':
                    action = f'<form method="POST" action="/update_test_results/{sample[1]}" style="display:inline;"><button type="submit">Update Results</button></form>'
                elif sample[8] == 'tested':
                    action = f'<a href="/send_results/{sample[1]}" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Send Results</a>'
                samples_html += f'<tr><td>{sample[1]}</td><td><a href="/patient/{sample[-2]}">{sample[-4]} {sample[-3]} ({sample[-2]})</a></td><td>{sample[7]}</td><td>{sample[8]}</td><td>{sample[6]}</td><td>{action}</td></tr>'
            samples_html += '</table>'
        else:
            samples_html = '<p>No blood samples collected yet.</p>'
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Blood Samples</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ color: #007bff; text-decoration: none; margin-right: 10px; }}
                table {{ margin: 20px 0; }}
                th, td {{ padding: 8px; text-align: left; }}
                button {{ background: #007bff; color: white; padding: 5px 10px; border: none; border-radius: 3px; cursor: pointer; }}
                button:hover {{ background: #0056b3; }}
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/">← Dashboard</a>
            </div>
            <h2>Blood Samples</h2>
            {samples_html}
        </body>
        </html>
        '''
        self.send_html_response(html)
    
    def send_search_patient_form(self):
        """Send search patient form"""
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Search Patient</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .form { max-width: 400px; margin: 0 auto; }
                .field { margin: 15px 0; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }
                .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; width: 100%; }
                .btn:hover { background: #0056b3; }
                .nav { margin-bottom: 20px; }
                .nav a { color: #007bff; text-decoration: none; margin-right: 10px; }
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/">← Back to Dashboard</a>
            </div>
            <div class="form">
                <h2>Search Patient</h2>
                <form method="POST" action="/search_patient">
                    <div class="field">
                        <label>Patient ID</label>
                        <input type="text" name="patient_id" placeholder="Enter Patient ID (e.g., PAT000001)" required>
                    </div>
                    <button type="submit" class="btn">Search Patient</button>
                </form>
                <hr>
                <div style="text-align: center;">
                    <p>Or</p>
                    <a href="/patients" class="btn" style="text-decoration: none; display: inline-block;">Browse All Patients</a>
                </div>
            </div>
        </body>
        </html>
        '''
        self.send_html_response(html)
    
    def send_add_location_form(self):
        """Send add location form"""
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Add Location</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .form { max-width: 400px; margin: 0 auto; }
                .field { margin: 15px 0; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }
                .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; }
                .btn:hover { background: #0056b3; }
                .nav { margin-bottom: 20px; }
                .nav a { color: #007bff; text-decoration: none; margin-right: 10px; }
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/">← Dashboard</a> | <a href="/locations">Locations</a>
            </div>
            <div class="form">
                <h2>Add New Location</h2>
                <form method="POST" action="/add_location">
                    <div class="field">
                        <label>Location Name *</label>
                        <input type="text" name="name" required>
                    </div>
                    <div class="field">
                        <label>Address</label>
                        <textarea name="address" rows="3"></textarea>
                    </div>
                    <div class="field">
                        <label>Phone</label>
                        <input type="tel" name="phone">
                    </div>
                    <button type="submit" class="btn">Add Location</button>
                </form>
            </div>
        </body>
        </html>
        '''
        self.send_html_response(html)
    
    def handle_search_patient(self, data):
        """Handle patient search"""
        patient_id = data['patient_id'][0].strip().upper()
        # Redirect to patient details
        self.send_response(302)
        self.send_header('Location', f'/patient/{patient_id}')
        self.end_headers()
    
    def handle_add_location(self, data):
        """Handle adding a new location"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO locations (name, address, phone)
                VALUES (?, ?, ?)
            ''', (
                data['name'][0],
                data.get('address', [''])[0],
                data.get('phone', [''])[0]
            ))
            conn.commit()
            conn.close()
            
            # Redirect to locations list
            self.send_response(302)
            self.send_header('Location', '/locations')
            self.end_headers()
            
        except Exception as e:
            self.send_error(500, f"Failed to add location: {str(e)}")
    
    def send_add_health_record_form(self, patient_id):
        """Send add health record form"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get patient info
        cursor.execute('SELECT * FROM patients WHERE patient_id = ?', (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            self.send_error(404, "Patient not found")
            return
        
        # Get locations
        cursor.execute('SELECT id, name FROM locations')
        locations = cursor.fetchall()
        conn.close()
        
        location_options = ''.join([f'<option value="{loc[0]}">{loc[1]}</option>' for loc in locations])
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Add Health Record</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .form {{ max-width: 600px; margin: 0 auto; }}
                .field {{ margin: 15px 0; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input, select, textarea {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }}
                .btn {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; }}
                .btn:hover {{ background: #0056b3; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ color: #007bff; text-decoration: none; margin-right: 10px; }}
                .row {{ display: flex; gap: 20px; }}
                .col {{ flex: 1; }}
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/patient/{patient_id}">← Back to Patient</a>
            </div>
            <div class="form">
                <h2>Add Health Record</h2>
                <p><strong>Patient:</strong> {patient[2]} {patient[3]} ({patient[1]})</p>
                <form method="POST" action="/add_health_record/{patient_id}">
                    <div class="row">
                        <div class="col">
                            <div class="field">
                                <label>Current Location *</label>
                                <select name="location_id" required>
                                    <option value="">Select Location</option>
                                    {location_options}
                                </select>
                            </div>
                        </div>
                        <div class="col">
                            <div class="field">
                                <label>Recorded By *</label>
                                <input type="text" name="recorded_by" required>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col">
                            <div class="field">
                                <label>Height (cm)</label>
                                <input type="number" step="0.1" name="height">
                            </div>
                        </div>
                        <div class="col">
                            <div class="field">
                                <label>Weight (kg)</label>
                                <input type="number" step="0.1" name="weight">
                            </div>
                        </div>
                        <div class="col">
                            <div class="field">
                                <label>Temperature (°C)</label>
                                <input type="number" step="0.1" name="temperature">
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col">
                            <div class="field">
                                <label>BP Systolic</label>
                                <input type="number" name="bp_systolic">
                            </div>
                        </div>
                        <div class="col">
                            <div class="field">
                                <label>BP Diastolic</label>
                                <input type="number" name="bp_diastolic">
                            </div>
                        </div>
                        <div class="col">
                            <div class="field">
                                <label>Heart Rate (bpm)</label>
                                <input type="number" name="heart_rate">
                            </div>
                        </div>
                    </div>
                    
                    <div class="field">
                        <label>Notes</label>
                        <textarea name="notes" rows="4"></textarea>
                    </div>
                    
                    <button type="submit" class="btn">Save Health Record</button>
                </form>
            </div>
        </body>
        </html>
        '''
        self.send_html_response(html)
    
    def handle_add_health_record(self, patient_id, data):
        """Handle adding health record"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            # Get patient internal ID
            cursor.execute('SELECT id FROM patients WHERE patient_id = ?', (patient_id,))
            patient = cursor.fetchone()
            
            if not patient:
                self.send_error(404, "Patient not found")
                return
            
            cursor.execute('''
                INSERT INTO health_records 
                (patient_id, location_id, height, weight, temperature, blood_pressure_systolic, 
                 blood_pressure_diastolic, heart_rate, notes, recorded_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient[0],
                data['location_id'][0],
                float(data['height'][0]) if data.get('height', [''])[0] else None,
                float(data['weight'][0]) if data.get('weight', [''])[0] else None,
                float(data['temperature'][0]) if data.get('temperature', [''])[0] else None,
                int(data['bp_systolic'][0]) if data.get('bp_systolic', [''])[0] else None,
                int(data['bp_diastolic'][0]) if data.get('bp_diastolic', [''])[0] else None,
                int(data['heart_rate'][0]) if data.get('heart_rate', [''])[0] else None,
                data.get('notes', [''])[0],
                data['recorded_by'][0]
            ))
            conn.commit()
            conn.close()
            
            # Redirect back to patient details
            self.send_response(302)
            self.send_header('Location', f'/patient/{patient_id}')
            self.end_headers()
            
        except Exception as e:
            self.send_error(500, f"Failed to add health record: {str(e)}")
    
    def send_collect_blood_sample_form(self, patient_id):
        """Send collect blood sample form"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get patient info
        cursor.execute('SELECT * FROM patients WHERE patient_id = ?', (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            self.send_error(404, "Patient not found")
            return
        
        # Get locations
        cursor.execute('SELECT id, name FROM locations')
        locations = cursor.fetchall()
        conn.close()
        
        location_options = ''.join([f'<option value="{loc[0]}">{loc[1]}</option>' for loc in locations])
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Collect Blood Sample</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .form {{ max-width: 500px; margin: 0 auto; }}
                .field {{ margin: 15px 0; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input, select {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }}
                .btn {{ background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; }}
                .btn:hover {{ background: #218838; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ color: #007bff; text-decoration: none; margin-right: 10px; }}
                .alert {{ background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 3px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/patient/{patient_id}">← Back to Patient</a>
            </div>
            <div class="form">
                <h2>Collect Blood Sample</h2>
                <p><strong>Patient:</strong> {patient[2]} {patient[3]} ({patient[1]})</p>
                <form method="POST" action="/collect_blood_sample/{patient_id}">
                    <div class="field">
                        <label>Collection Location *</label>
                        <select name="collection_location_id" required>
                            <option value="">Select Location</option>
                            {location_options}
                        </select>
                    </div>
                    
                    <div class="field">
                        <label>Test Type *</label>
                        <select name="test_type" required>
                            <option value="">Select Test Type</option>
                            <option value="Complete Blood Count (CBC)">Complete Blood Count (CBC)</option>
                            <option value="Blood Sugar">Blood Sugar</option>
                            <option value="Cholesterol">Cholesterol</option>
                            <option value="Liver Function Test">Liver Function Test</option>
                            <option value="Kidney Function Test">Kidney Function Test</option>
                            <option value="Thyroid Function Test">Thyroid Function Test</option>
                            <option value="HIV Test">HIV Test</option>
                            <option value="Hepatitis Panel">Hepatitis Panel</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    
                    <div class="field">
                        <label>Collected By *</label>
                        <input type="text" name="collected_by" required>
                    </div>
                    
                    <div class="alert">
                        <strong>Note:</strong> A unique sample ID will be automatically generated upon collection.
                        The sample will be flagged for testing and can be processed at any location.
                    </div>
                    
                    <button type="submit" class="btn">Collect Sample</button>
                </form>
            </div>
        </body>
        </html>
        '''
        self.send_html_response(html)
    
    def handle_collect_blood_sample(self, patient_id, data):
        """Handle blood sample collection"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            # Get patient internal ID
            cursor.execute('SELECT id FROM patients WHERE patient_id = ?', (patient_id,))
            patient = cursor.fetchone()
            
            if not patient:
                self.send_error(404, "Patient not found")
                return
            
            sample_id = generate_sample_id()
            
            cursor.execute('''
                INSERT INTO blood_samples 
                (sample_id, patient_id, collection_location_id, test_type, collected_by, status)
                VALUES (?, ?, ?, ?, ?, 'collected')
            ''', (
                sample_id,
                patient[0],
                data['collection_location_id'][0],
                data['test_type'][0],
                data['collected_by'][0]
            ))
            conn.commit()
            conn.close()
            
            # Redirect back to patient details
            self.send_response(302)
            self.send_header('Location', f'/patient/{patient_id}')
            self.end_headers()
            
        except Exception as e:
            self.send_error(500, f"Failed to collect blood sample: {str(e)}")
    
    def send_update_test_results_form(self, sample_id):
        """Send update test results form"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get sample info
        cursor.execute('''
            SELECT bs.*, p.first_name, p.last_name, p.patient_id 
            FROM blood_samples bs
            JOIN patients p ON bs.patient_id = p.id
            WHERE bs.sample_id = ?
        ''', (sample_id,))
        sample = cursor.fetchone()
        
        if not sample:
            self.send_error(404, "Sample not found")
            return
        
        # Get locations
        cursor.execute('SELECT id, name FROM locations')
        locations = cursor.fetchall()
        conn.close()
        
        location_options = ''.join([f'<option value="{loc[0]}">{loc[1]}</option>' for loc in locations])
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Update Test Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .form {{ max-width: 600px; margin: 0 auto; }}
                .field {{ margin: 15px 0; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input, select, textarea {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }}
                .btn {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; }}
                .btn:hover {{ background: #0056b3; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ color: #007bff; text-decoration: none; margin-right: 10px; }}
                .row {{ display: flex; gap: 20px; }}
                .col {{ flex: 1; }}
                .alert {{ background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 3px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/blood_samples">← Back to Blood Samples</a>
            </div>
            <div class="form">
                <h2>Update Test Results</h2>
                <p><strong>Sample ID:</strong> {sample[1]}</p>
                <p><strong>Patient:</strong> {sample[-3]} {sample[-2]} ({sample[-1]})</p>
                <p><strong>Test Type:</strong> {sample[7]}</p>
                <form method="POST" action="/update_test_results/{sample_id}">
                    <div class="row">
                        <div class="col">
                            <div class="field">
                                <label>Test Location *</label>
                                <select name="test_location_id" required>
                                    <option value="">Select Location</option>
                                    {location_options}
                                </select>
                            </div>
                        </div>
                        <div class="col">
                            <div class="field">
                                <label>Tested By *</label>
                                <input type="text" name="tested_by" required value="{sample[10] or ''}">
                            </div>
                        </div>
                    </div>
                    
                    <div class="field">
                        <label>Test Results *</label>
                        <textarea name="results" rows="10" required>{sample[9] or ''}</textarea>
                    </div>
                    
                    <div class="alert">
                        <strong>Note:</strong> Once results are saved, they can be sent to the patient via WhatsApp.
                    </div>
                    
                    <button type="submit" class="btn">Save Results</button>
                </form>
            </div>
        </body>
        </html>
        '''
        self.send_html_response(html)
    
    def handle_update_test_results(self, sample_id, data):
        """Handle updating test results"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE blood_samples 
                SET test_location_id = ?, results = ?, tested_by = ?, 
                    tested_at = CURRENT_TIMESTAMP, status = 'tested'
                WHERE sample_id = ?
            ''', (
                data['test_location_id'][0],
                data['results'][0],
                data['tested_by'][0],
                sample_id
            ))
            conn.commit()
            conn.close()
            
            # Redirect back to blood samples
            self.send_response(302)
            self.send_header('Location', '/blood_samples')
            self.end_headers()
            
        except Exception as e:
            self.send_error(500, f"Failed to update test results: {str(e)}")
    
    def handle_send_results(self, sample_id):
        """Handle sending test results via WhatsApp"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            # Get sample and patient info
            cursor.execute('''
                SELECT bs.*, p.first_name, p.last_name, p.patient_id, p.phone 
                FROM blood_samples bs
                JOIN patients p ON bs.patient_id = p.id
                WHERE bs.sample_id = ? AND bs.status = 'tested'
            ''', (sample_id,))
            sample = cursor.fetchone()
            
            if not sample:
                self.send_error(404, "Sample not found or not tested")
                return
            
            # Format WhatsApp message
            message = f"""
🏥 MEDICAL TEST RESULTS 🏥

Patient: {sample[-4]} {sample[-3]}
Patient ID: {sample[-2]}
Sample ID: {sample[1]}
Test Type: {sample[7]}

Results:
{sample[9]}

Tested by: {sample[10]}
Test Date: {sample[11]}

For questions, please contact your healthcare provider.
            """
            
            # Simulate WhatsApp sending
            success = simulate_whatsapp_send(sample[-1], message)
            
            if success:
                # Update status to results_sent
                cursor.execute('''
                    UPDATE blood_samples 
                    SET status = 'results_sent', results_sent_at = CURRENT_TIMESTAMP
                    WHERE sample_id = ?
                ''', (sample_id,))
                conn.commit()
            
            conn.close()
            
            # Redirect back to blood samples with success message
            self.send_response(302)
            self.send_header('Location', '/blood_samples')
            self.end_headers()
            
        except Exception as e:
            self.send_error(500, f"Failed to send results: {str(e)}")

# Additional handler methods would go here...

def main():
    """Main function to start the server"""
    # Initialize database
    init_database()
    
    # Start HTTP server
    PORT = 8000
    with socketserver.TCPServer(("", PORT), DemographicHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()