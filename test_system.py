#!/usr/bin/env python3
"""
Simple test script for the Patient Demographic System
Tests the core functionality without external dependencies
"""

import sqlite3
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import init_database, generate_patient_id, generate_sample_id

def test_database_setup():
    """Test database initialization"""
    print("Testing database setup...")
    
    # Remove existing test database
    test_db = 'test_demographic.db'
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Test with different database
    import app
    app.DATABASE = test_db
    init_database()
    
    # Check if tables exist
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ['locations', 'patients', 'health_records', 'blood_samples']
    for table in expected_tables:
        assert table in tables, f"Table {table} not found"
    
    # Check if default location was created
    cursor.execute("SELECT COUNT(*) FROM locations")
    location_count = cursor.fetchone()[0]
    assert location_count > 0, "No default location created"
    
    conn.close()
    print("✓ Database setup test passed")

def test_patient_registration():
    """Test patient registration"""
    print("Testing patient registration...")
    
    test_db = 'test_demographic.db'
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # Test patient ID generation
    patient_id = generate_patient_id()
    assert patient_id == "PAT000001", f"Expected PAT000001, got {patient_id}"
    
    # Register a test patient
    cursor.execute('''
        INSERT INTO patients 
        (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, emergency_contact, location_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        patient_id, "Test", "Patient", "1990-01-01", "Male", "+1234567890", 
        "test@email.com", "123 Test St", "+0987654321", 1
    ))
    conn.commit()
    
    # Verify patient was created
    cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    patient = cursor.fetchone()
    assert patient is not None, "Patient not found after registration"
    assert patient[2] == "Test", "Patient first name incorrect"
    
    conn.close()
    print("✓ Patient registration test passed")

def test_health_records():
    """Test health record functionality"""
    print("Testing health records...")
    
    test_db = 'test_demographic.db'
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # Add a health record
    cursor.execute('''
        INSERT INTO health_records 
        (patient_id, location_id, height, weight, temperature, blood_pressure_systolic, 
         blood_pressure_diastolic, heart_rate, notes, recorded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (1, 1, 175.5, 70.2, 36.8, 120, 80, 72, "Test health record", "Dr. Test"))
    conn.commit()
    
    # Verify health record was created
    cursor.execute("SELECT * FROM health_records WHERE patient_id = 1")
    record = cursor.fetchone()
    assert record is not None, "Health record not found"
    assert record[3] == 175.5, "Height value incorrect"
    
    conn.close()
    print("✓ Health records test passed")

def test_blood_samples():
    """Test blood sample functionality"""
    print("Testing blood samples...")
    
    test_db = 'test_demographic.db'
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # Test sample ID generation
    sample_id = generate_sample_id()
    assert sample_id == "BS000001", f"Expected BS000001, got {sample_id}"
    
    # Collect a blood sample
    cursor.execute('''
        INSERT INTO blood_samples 
        (sample_id, patient_id, collection_location_id, test_type, collected_by, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (sample_id, 1, 1, "Complete Blood Count (CBC)", "Lab Tech Test", "collected"))
    conn.commit()
    
    # Verify sample was created
    cursor.execute("SELECT * FROM blood_samples WHERE sample_id = ?", (sample_id,))
    sample = cursor.fetchone()
    assert sample is not None, "Blood sample not found"
    assert sample[8] == "collected", "Sample status incorrect"
    
    # Update test results
    cursor.execute('''
        UPDATE blood_samples 
        SET test_location_id = ?, results = ?, tested_by = ?, status = 'tested'
        WHERE sample_id = ?
    ''', (1, "Test results: All normal", "Dr. Lab Test", sample_id))
    conn.commit()
    
    # Verify results were updated
    cursor.execute("SELECT * FROM blood_samples WHERE sample_id = ?", (sample_id,))
    sample = cursor.fetchone()
    assert sample[8] == "tested", "Sample status not updated"
    assert sample[9] == "Test results: All normal", "Test results not saved"
    
    conn.close()
    print("✓ Blood samples test passed")

def run_all_tests():
    """Run all tests"""
    print("Running Patient Demographic System Tests")
    print("=" * 50)
    
    try:
        test_database_setup()
        test_patient_registration()
        test_health_records()
        test_blood_samples()
        
        print("=" * 50)
        print("✓ All tests passed successfully!")
        print("The Patient Demographic System is working correctly.")
        
        # Clean up test database
        test_db = 'test_demographic.db'
        if os.path.exists(test_db):
            os.remove(test_db)
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)