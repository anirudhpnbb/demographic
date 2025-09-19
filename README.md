# Patient Demographic and Health Management System

A comprehensive web-based system for managing patient demographics, health records, blood samples, and test results across multiple healthcare locations. The system supports patient registration, health tracking, blood sample collection/testing, and automated WhatsApp notifications for test results.

## Features

### Core Functionality
- **Patient Registration**: Register patients with unique IDs (PAT000001 format)
- **Multi-Location Support**: Manage patients across different healthcare facilities
- **Health Records**: Track height, weight, temperature, blood pressure, heart rate, and notes
- **Blood Sample Management**: Collect, track, and test blood samples with unique IDs (BS000001 format)
- **Test Results**: Update and manage laboratory test results
- **WhatsApp Notifications**: Send test results to patients via WhatsApp (simulated)
- **QR Code Generation**: Each patient gets a unique QR code for quick access

### Key Features
- **Cross-Location Access**: Patient data accessible from any location using patient ID
- **Real-time Status Tracking**: Track blood sample status (collected → tested → results_sent)
- **Comprehensive Dashboard**: Overview statistics and recent patient activity
- **Patient Search**: Quick patient lookup by ID
- **Audit Trail**: Complete history of health records and test results

## System Architecture

The system uses a simplified architecture with minimal dependencies:
- **Backend**: Pure Python HTTP server (no Flask/Django required)
- **Database**: SQLite for data storage
- **Frontend**: HTML/CSS with responsive design
- **Dependencies**: Only standard Python libraries

## Database Schema

### Tables
1. **locations** - Healthcare facility information
2. **patients** - Patient demographic data
3. **health_records** - Medical measurements and observations
4. **blood_samples** - Sample collection and test result tracking

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- No external dependencies required (uses only standard Python libraries)

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd demographic
   ```

2. Run the application:
   ```bash
   python3 app.py
   ```

3. Access the system at: http://localhost:8000

### Optional Dependencies
For enhanced QR code generation, install:
```bash
pip install qrcode[pil]
```

## Usage

### 1. Patient Registration
1. Click "Register New Patient" on the dashboard
2. Fill in patient demographics (name, DOB, gender, phone, etc.)
3. Select registration location
4. Patient receives unique ID (e.g., PAT000001)

### 2. Health Record Entry
1. Search for patient by ID or browse patient list
2. Click "Add Health Record" on patient details page
3. Enter vital signs (height, weight, temperature, BP, heart rate)
4. Add notes and specify healthcare provider
5. Record is saved and displayed in patient history

### 3. Blood Sample Collection
1. From patient details page, click "Collect Blood Sample"
2. Select collection location and test type
3. Enter collector name
4. Sample receives unique ID (e.g., BS000001)
5. Sample status set to "collected"

### 4. Test Result Processing
1. Go to "Blood Samples" section
2. Find sample with "collected" status
3. Click "Update Results"
4. Enter test location, technician name, and detailed results
5. Status changes to "tested"

### 5. WhatsApp Notification
1. For samples with "tested" status, click "Send Results"
2. System simulates WhatsApp message to patient
3. Status changes to "results_sent"
4. Message includes patient info, test results, and contact information

## API Endpoints

### Patient Management
- `GET /` - Dashboard with system overview
- `GET /register_patient` - Patient registration form
- `POST /register_patient` - Submit new patient registration
- `GET /patients` - List all patients
- `GET /patient/<patient_id>` - Patient details and history
- `GET /search_patient` - Patient search form
- `POST /search_patient` - Search for patient by ID

### Health Records
- `GET /add_health_record/<patient_id>` - Health record form
- `POST /add_health_record/<patient_id>` - Submit health record

### Blood Samples
- `GET /collect_blood_sample/<patient_id>` - Blood collection form
- `POST /collect_blood_sample/<patient_id>` - Submit blood sample collection
- `GET /blood_samples` - List all blood samples
- `GET /update_test_results/<sample_id>` - Test results form
- `POST /update_test_results/<sample_id>` - Submit test results
- `GET /send_results/<sample_id>` - Send WhatsApp notification

### Location Management
- `GET /locations` - List all locations
- `GET /add_location` - Add location form
- `POST /add_location` - Submit new location

## Configuration

The system uses SQLite database (`demographic.db`) which is automatically created on first run. Default location "Main Hospital" is created automatically.

### WhatsApp Integration
Currently implemented as simulation. For production use:
1. Replace `simulate_whatsapp_send()` function with WhatsApp Business API
2. Configure API credentials
3. Update message formatting as needed

## Testing

Run the included test suite:
```bash
python3 test_system.py
```

Tests cover:
- Database setup and table creation
- Patient registration workflow
- Health record management
- Blood sample collection and testing
- ID generation algorithms

## Security Considerations

- Input validation on all forms
- SQL injection prevention using parameterized queries
- No sensitive data stored in logs
- Patient data access control by location

## Deployment

For production deployment:
1. Use proper WSGI server (e.g., Gunicorn)
2. Configure HTTPS/SSL
3. Set up proper database (PostgreSQL/MySQL)
4. Implement user authentication and authorization
5. Configure real WhatsApp Business API
6. Set up backup and monitoring

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository or contact the development team.