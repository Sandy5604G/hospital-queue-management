"""
Database Management Module for Hospital Queue System
Handles all SQLite database operations
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional

class HospitalDatabase:
    def __init__(self, db_name: str = 'hospital_queue.db'):
        """
        Initialize database connection
        Args:
            db_name: Name of the SQLite database file
        """
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Create and return a database connection
        """
        conn = sqlite3.connect(self.db_name)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def init_database(self) -> None:
        """
        Initialize database tables if they don't exist
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Patients table - Core patient information
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_number VARCHAR(10) UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    age INTEGER,
                    gender VARCHAR(10) CHECK(gender IN ('Male', 'Female', 'Other')),
                    phone_number VARCHAR(15),
                    emergency_contact VARCHAR(15),
                    medical_condition TEXT,
                    priority_level INTEGER NOT NULL CHECK(priority_level BETWEEN 1 AND 3),
                    department VARCHAR(50),
                    doctor_assigned VARCHAR(50),
                    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    consultation_start_time TIMESTAMP,
                    consultation_end_time TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'waiting' 
                        CHECK(status IN ('waiting', 'in_consultation', 'completed', 'cancelled')),
                    estimated_wait_time INTEGER,  -- in minutes
                    notes TEXT,
                    is_emergency BOOLEAN DEFAULT 0,
                    is_follow_up BOOLEAN DEFAULT 0
                )
            ''')
            
            # Departments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS departments (
                    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    department_name VARCHAR(50) UNIQUE NOT NULL,
                    department_code VARCHAR(10) UNIQUE NOT NULL,
                    current_wait_time INTEGER DEFAULT 30,  -- in minutes
                    active_doctors INTEGER DEFAULT 1
                )
            ''')
            
            # Doctors table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doctors (
                    doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_name VARCHAR(100) NOT NULL,
                    department_id INTEGER,
                    specialization TEXT,
                    is_available BOOLEAN DEFAULT 1,
                    current_patient_token VARCHAR(10),
                    FOREIGN KEY (department_id) REFERENCES departments(department_id)
                )
            ''')
            
            # Queue History table - Tracks all queue movements
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS queue_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_number VARCHAR(10) NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    previous_status VARCHAR(20),
                    new_status VARCHAR(20),
                    queue_position_before INTEGER,
                    queue_position_after INTEGER,
                    performed_by VARCHAR(50) DEFAULT 'system',
                    notes TEXT,
                    FOREIGN KEY (token_number) REFERENCES patients(token_number)
                )
            ''')
            
            # Statistics table - For analytics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    total_patients INTEGER DEFAULT 0,
                    emergency_cases INTEGER DEFAULT 0,
                    regular_cases INTEGER DEFAULT 0,
                    follow_up_cases INTEGER DEFAULT 0,
                    avg_wait_time INTEGER DEFAULT 0,
                    max_wait_time INTEGER DEFAULT 0,
                    min_wait_time INTEGER DEFAULT 0,
                    doctors_available INTEGER DEFAULT 0,
                    peak_hour TIME,
                    department_breakdown TEXT  -- JSON format
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patients_status ON patients(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patients_priority ON patients(priority_level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patients_token ON patients(token_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_queue_history_token ON queue_history(token_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_queue_history_time ON queue_history(action_time)')
            
            # Insert default departments if empty
            cursor.execute('SELECT COUNT(*) FROM departments')
            if cursor.fetchone()[0] == 0:
                default_departments = [
                    ('Emergency', 'ER', 15, 3),
                    ('General Medicine', 'GM', 45, 2),
                    ('Pediatrics', 'PED', 30, 2),
                    ('Cardiology', 'CARD', 60, 1),
                    ('Orthopedics', 'ORTH', 40, 1),
                    ('Dermatology', 'DERM', 25, 1)
                ]
                cursor.executemany('''
                    INSERT INTO departments 
                    (department_name, department_code, current_wait_time, active_doctors)
                    VALUES (?, ?, ?, ?)
                ''', default_departments)
            
            # Insert default doctors if empty
            cursor.execute('SELECT COUNT(*) FROM doctors')
            if cursor.fetchone()[0] == 0:
                default_doctors = [
                    ('Dr. Smith', 1, 'Emergency Medicine', 1, None),
                    ('Dr. Johnson', 1, 'Trauma Specialist', 1, None),
                    ('Dr. Williams', 2, 'General Physician', 1, None),
                    ('Dr. Brown', 3, 'Pediatrician', 1, None),
                    ('Dr. Davis', 4, 'Cardiologist', 1, None)
                ]
                cursor.executemany('''
                    INSERT INTO doctors 
                    (doctor_name, department_id, specialization, is_available, current_patient_token)
                    VALUES (?, ?, ?, ?, ?)
                ''', default_doctors)
            
            conn.commit()
    
    def generate_token(self, department_code: str = None) -> str:
        """
        Generate unique token number
        Format: [DepartmentCode]-[Date]-[SequenceNumber]
        Example: GM-20231225-001
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y%m%d')
            
            if department_code:
                prefix = f"{department_code}-{today}-"
            else:
                prefix = f"HOSP-{today}-"
            
            # Get the last token for today
            cursor.execute('''
                SELECT token_number FROM patients 
                WHERE token_number LIKE ? 
                ORDER BY token_number DESC LIMIT 1
            ''', (f'{prefix}%',))
            
            result = cursor.fetchone()
            
            if result:
                last_number = int(result[0].split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            return f"{prefix}{new_number:03d}"
    
    def add_patient(self, patient_data: Dict[str, Any]) -> str:
        """
        Add a new patient to the system
        Returns: Generated token number
        """
        token = self.generate_token(patient_data.get('department_code'))
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate estimated wait time
            estimated_wait = self.calculate_wait_time(
                patient_data.get('priority_level', 2),
                patient_data.get('department')
            )
            
            cursor.execute('''
                INSERT INTO patients (
                    token_number, full_name, age, gender, phone_number,
                    emergency_contact, medical_condition, priority_level,
                    department, is_emergency, is_follow_up,
                    estimated_wait_time, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                token,
                patient_data['full_name'],
                patient_data.get('age'),
                patient_data.get('gender'),
                patient_data.get('phone_number'),
                patient_data.get('emergency_contact'),
                patient_data.get('medical_condition'),
                patient_data.get('priority_level', 2),
                patient_data.get('department'),
                1 if patient_data.get('priority_level') == 1 else 0,
                1 if patient_data.get('is_follow_up') else 0,
                estimated_wait,
                patient_data.get('notes')
            ))
            
            # Log the registration in history
            cursor.execute('''
                INSERT INTO queue_history (
                    token_number, action, previous_status, new_status,
                    queue_position_before, queue_position_after
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                token, 'REGISTERED', None, 'waiting', 
                None, self.get_queue_position(token)
            ))
            
            conn.commit()
        
        return token
    
    def calculate_wait_time(self, priority: int, department: str = None) -> int:
        """
        Calculate estimated wait time based on priority and department
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get number of patients ahead
            if department:
                cursor.execute('''
                    SELECT COUNT(*) FROM patients 
                    WHERE status = 'waiting' 
                    AND department = ?
                    AND (priority_level > ? OR (priority_level = ? AND registration_time < CURRENT_TIMESTAMP))
                ''', (department, priority, priority))
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM patients 
                    WHERE status = 'waiting' 
                    AND (priority_level > ? OR (priority_level = ? AND registration_time < CURRENT_TIMESTAMP))
                ''', (priority, priority))
            
            patients_ahead = cursor.fetchone()[0]
            
            # Base wait time based on priority
            if priority == 1:  # Emergency
                base_time = 0
            elif priority == 2:  # Regular
                base_time = 20
            else:  # Follow-up
                base_time = 10
            
            # Department-specific adjustments
            if department:
                cursor.execute('SELECT current_wait_time FROM departments WHERE department_name = ?', (department,))
                dept_result = cursor.fetchone()
                if dept_result:
                    base_time += dept_result[0]
            
            total_wait = base_time + (patients_ahead * 15)  # 15 minutes per patient ahead
            
            return min(total_wait, 240)  # Max 4 hours
    
    def get_queue_position(self, token_number: str) -> int:
        """
        Get current position in queue for a patient
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT priority_level, registration_time 
                FROM patients WHERE token_number = ?
            ''', (token_number,))
            
            patient = cursor.fetchone()
            if not patient:
                return -1
            
            priority, reg_time = patient
            
            cursor.execute('''
                SELECT COUNT(*) FROM patients 
                WHERE status = 'waiting'
                AND (priority_level < ? OR (priority_level = ? AND registration_time < ?))
            ''', (priority, priority, reg_time))
            
            position = cursor.fetchone()[0] + 1  # +1 because position starts from 1
            
            return position
    
    def get_current_queue(self, department: str = None) -> List[Tuple]:
        """
        Get current waiting queue
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if department:
                cursor.execute('''
                    SELECT p.token_number, p.full_name, p.priority_level, 
                           p.registration_time, p.estimated_wait_time,
                           p.department, p.medical_condition,
                           CASE p.priority_level
                               WHEN 1 THEN 'Emergency'
                               WHEN 2 THEN 'Regular'
                               WHEN 3 THEN 'Follow-up'
                           END as priority_text
                    FROM patients p
                    WHERE p.status = 'waiting'
                    AND p.department = ?
                    ORDER BY p.priority_level ASC, p.registration_time ASC
                ''', (department,))
            else:
                cursor.execute('''
                    SELECT p.token_number, p.full_name, p.priority_level, 
                           p.registration_time, p.estimated_wait_time,
                           p.department, p.medical_condition,
                           CASE p.priority_level
                               WHEN 1 THEN 'Emergency'
                               WHEN 2 THEN 'Regular'
                               WHEN 3 THEN 'Follow-up'
                           END as priority_text
                    FROM patients p
                    WHERE p.status = 'waiting'
                    ORDER BY p.priority_level ASC, p.registration_time ASC
                ''')
            
            return cursor.fetchall()
    
    def get_current_patient(self) -> Optional[Tuple]:
        """
        Get the patient currently in consultation
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT p.token_number, p.full_name, p.department,
                       d.doctor_name, p.consultation_start_time
                FROM patients p
                LEFT JOIN doctors d ON p.doctor_assigned = d.doctor_name
                WHERE p.status = 'in_consultation'
                ORDER BY p.consultation_start_time ASC
                LIMIT 1
            ''')
            
            return cursor.fetchone()
    
    def get_next_patient(self) -> Optional[Tuple]:
        """
        Get the next patient to be called
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT token_number, full_name, department, priority_level,
                       estimated_wait_time, medical_condition
                FROM patients
                WHERE status = 'waiting'
                ORDER BY priority_level ASC, registration_time ASC
                LIMIT 1
            ''')
            
            return cursor.fetchone()
    
    def start_consultation(self, token_number: str, doctor_name: str = None) -> bool:
        """
        Mark patient as in consultation
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current queue position before update
            old_position = self.get_queue_position(token_number)
            
            cursor.execute('''
                UPDATE patients 
                SET status = 'in_consultation',
                    consultation_start_time = CURRENT_TIMESTAMP,
                    doctor_assigned = ?
                WHERE token_number = ? AND status = 'waiting'
            ''', (doctor_name, token_number))
            
            rows_affected = cursor.rowcount
            
            if rows_affected > 0:
                # Log the action
                cursor.execute('''
                    INSERT INTO queue_history (
                        token_number, action, previous_status, new_status,
                        queue_position_before, queue_position_after
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    token_number, 'CONSULTATION_STARTED', 'waiting', 'in_consultation',
                    old_position, None
                ))
                
                # Update doctor's current patient
                if doctor_name:
                    cursor.execute('''
                        UPDATE doctors 
                        SET current_patient_token = ?, is_available = 0
                        WHERE doctor_name = ?
                    ''', (token_number, doctor_name))
                
                conn.commit()
                return True
            
            return False
    
    def complete_consultation(self, token_number: str) -> bool:
        """
        Mark patient consultation as completed
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get doctor assigned to this patient
            cursor.execute('SELECT doctor_assigned FROM patients WHERE token_number = ?', (token_number,))
            doctor_result = cursor.fetchone()
            doctor_name = doctor_result[0] if doctor_result else None
            
            cursor.execute('''
                UPDATE patients 
                SET status = 'completed',
                    consultation_end_time = CURRENT_TIMESTAMP
                WHERE token_number = ? AND status = 'in_consultation'
            ''', (token_number,))
            
            rows_affected = cursor.rowcount
            
            if rows_affected > 0:
                # Log the action
                cursor.execute('''
                    INSERT INTO queue_history (
                        token_number, action, previous_status, new_status
                    ) VALUES (?, ?, ?, ?)
                ''', (token_number, 'CONSULTATION_COMPLETED', 'in_consultation', 'completed'))
                
                # Free up the doctor
                if doctor_name:
                    cursor.execute('''
                        UPDATE doctors 
                        SET current_patient_token = NULL, is_available = 1
                        WHERE doctor_name = ?
                    ''', (doctor_name,))
                
                # Update statistics
                self.update_daily_statistics()
                
                conn.commit()
                return True
            
            return False
    
    def cancel_patient(self, token_number: str, reason: str = None) -> bool:
        """
        Cancel a patient's registration
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current status and position
            cursor.execute('SELECT status FROM patients WHERE token_number = ?', (token_number,))
            patient = cursor.fetchone()
            
            if not patient:
                return False
            
            old_status = patient[0]
            old_position = self.get_queue_position(token_number) if old_status == 'waiting' else None
            
            cursor.execute('''
                UPDATE patients 
                SET status = 'cancelled'
                WHERE token_number = ?
            ''', (token_number,))
            
            rows_affected = cursor.rowcount
            
            if rows_affected > 0:
                # Log the action
                cursor.execute('''
                    INSERT INTO queue_history (
                        token_number, action, previous_status, new_status,
                        queue_position_before, queue_position_after, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    token_number, 'CANCELLED', old_status, 'cancelled',
                    old_position, None, reason
                ))
                
                conn.commit()
                return True
            
            return False
    
    def get_patient_by_token(self, token_number: str) -> Optional[Dict[str, Any]]:
        """
        Get complete patient information by token
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    token_number, full_name, age, gender, phone_number,
                    emergency_contact, medical_condition, priority_level,
                    department, doctor_assigned, registration_time,
                    consultation_start_time, consultation_end_time,
                    status, estimated_wait_time, notes,
                    is_emergency, is_follow_up,
                    CASE priority_level
                        WHEN 1 THEN 'Emergency'
                        WHEN 2 THEN 'Regular'
                        WHEN 3 THEN 'Follow-up'
                    END as priority_text
                FROM patients
                WHERE token_number = ?
            ''', (token_number,))
            
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            
            if row:
                return dict(zip(columns, row))
            
            return None
    
    def get_queue_history(self, token_number: str = None, limit: int = 50) -> List[Tuple]:
        """
        Get queue history
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if token_number:
                cursor.execute('''
                    SELECT h.action_time, h.action, h.previous_status, h.new_status,
                           h.queue_position_before, h.queue_position_after, h.performed_by,
                           p.full_name
                    FROM queue_history h
                    LEFT JOIN patients p ON h.token_number = p.token_number
                    WHERE h.token_number = ?
                    ORDER BY h.action_time DESC
                    LIMIT ?
                ''', (token_number, limit))
            else:
                cursor.execute('''
                    SELECT h.action_time, h.action, h.previous_status, h.new_status,
                           h.queue_position_before, h.queue_position_after, h.performed_by,
                           p.full_name, h.token_number
                    FROM queue_history h
                    LEFT JOIN patients p ON h.token_number = p.token_number
                    ORDER BY h.action_time DESC
                    LIMIT ?
                ''', (limit,))
            
            return cursor.fetchall()
    
    def get_average_waiting_count(self, hours: int = 24) -> Dict[str, Any]:
        """
        Calculate average waiting statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_patients,
                    AVG(estimated_wait_time) as avg_wait_time,
                    MAX(estimated_wait_time) as max_wait_time,
                    MIN(estimated_wait_time) as min_wait_time,
                    SUM(CASE WHEN priority_level = 1 THEN 1 ELSE 0 END) as emergency_count,
                    SUM(CASE WHEN priority_level = 2 THEN 1 ELSE 0 END) as regular_count,
                    SUM(CASE WHEN priority_level = 3 THEN 1 ELSE 0 END) as follow_up_count
                FROM patients
                WHERE registration_time >= datetime('now', ?)
                AND status IN ('waiting', 'completed')
            ''', (f'-{hours} hours',))
            
            stats = cursor.fetchone()
            
            cursor.execute('''
                SELECT COUNT(*) FROM patients WHERE status = 'waiting'
            ''')
            current_waiting = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT department, COUNT(*) as count
                FROM patients
                WHERE status = 'waiting'
                GROUP BY department
                ORDER BY count DESC
            ''')
            department_breakdown = cursor.fetchall()
            
            return {
                'total_patients_last_24h': stats[0] if stats[0] else 0,
                'average_wait_time': round(stats[1], 1) if stats[1] else 0,
                'max_wait_time': stats[2] if stats[2] else 0,
                'min_wait_time': stats[3] if stats[3] else 0,
                'emergency_cases': stats[4] if stats[4] else 0,
                'regular_cases': stats[5] if stats[5] else 0,
                'follow_up_cases': stats[6] if stats[6] else 0,
                'currently_waiting': current_waiting,
                'department_breakdown': department_breakdown
            }
    
    def update_daily_statistics(self) -> None:
        """
        Update daily statistics table
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Check if today's stats already exist
            cursor.execute('SELECT COUNT(*) FROM statistics WHERE date = ?', (today,))
            if cursor.fetchone()[0] == 0:
                # Get stats for today
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN priority_level = 1 THEN 1 ELSE 0 END) as emergency,
                        SUM(CASE WHEN priority_level = 2 THEN 1 ELSE 0 END) as regular,
                        SUM(CASE WHEN priority_level = 3 THEN 1 ELSE 0 END) as follow_up,
                        AVG(
                            (julianday(consultation_start_time) - julianday(registration_time)) * 24 * 60
                        ) as avg_wait,
                        MAX(
                            (julianday(consultation_start_time) - julianday(registration_time)) * 24 * 60
                        ) as max_wait,
                        MIN(
                            (julianday(consultation_start_time) - julianday(registration_time)) * 24 * 60
                        ) as min_wait,
                        COUNT(DISTINCT doctor_assigned) as doctors_available
                    FROM patients
                    WHERE DATE(registration_time) = DATE('now')
                    AND status = 'completed'
                ''')
                
                stats = cursor.fetchone()
                
                # Get peak hour
                cursor.execute('''
                    SELECT strftime('%H:00', registration_time) as hour,
                           COUNT(*) as count
                    FROM patients
                    WHERE DATE(registration_time) = DATE('now')
                    GROUP BY hour
                    ORDER BY count DESC
                    LIMIT 1
                ''')
                peak_hour = cursor.fetchone()
                
                # Get department breakdown
                cursor.execute('''
                    SELECT department, COUNT(*) as count
                    FROM patients
                    WHERE DATE(registration_time) = DATE('now')
                    GROUP BY department
                ''')
                dept_breakdown = cursor.fetchall()
                
                # Insert new stats
                cursor.execute('''
                    INSERT INTO statistics (
                        date, total_patients, emergency_cases, regular_cases,
                        follow_up_cases, avg_wait_time, max_wait_time,
                        min_wait_time, doctors_available, peak_hour,
                        department_breakdown
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    today,
                    stats[0] if stats[0] else 0,
                    stats[1] if stats[1] else 0,
                    stats[2] if stats[2] else 0,
                    stats[3] if stats[3] else 0,
                    round(stats[4], 1) if stats[4] else 0,
                    round(stats[5], 1) if stats[5] else 0,
                    round(stats[6], 1) if stats[6] else 0,
                    stats[7] if stats[7] else 0,
                    peak_hour[0] if peak_hour else None,
                    str(dept_breakdown) if dept_breakdown else '[]'
                ))
                
                conn.commit()
    
    def get_available_doctors(self, department: str = None) -> List[Tuple]:
        """
        Get list of available doctors
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if department:
                cursor.execute('''
                    SELECT d.doctor_name, d.specialization, dept.department_name
                    FROM doctors d
                    JOIN departments dept ON d.department_id = dept.department_id
                    WHERE d.is_available = 1
                    AND dept.department_name = ?
                ''', (department,))
            else:
                cursor.execute('''
                    SELECT d.doctor_name, d.specialization, dept.department_name
                    FROM doctors d
                    JOIN departments dept ON d.department_id = dept.department_id
                    WHERE d.is_available = 1
                ''')
            
            return cursor.fetchall()
    
    def get_departments(self) -> List[Tuple]:
        """
        Get all departments
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT department_name, department_code, current_wait_time, active_doctors
                FROM departments
                ORDER BY department_name
            ''')
            
            return cursor.fetchall()
    
    def update_department_wait_time(self, department: str, wait_time: int) -> bool:
        """
        Update department's current wait time
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE departments 
                SET current_wait_time = ?
                WHERE department_name = ?
            ''', (wait_time, department))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def export_data(self, export_type: str = 'csv') -> str:
        """
        Export data to file
        """
        import csv
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_type.lower() == 'csv':
            filename = f'hospital_queue_export_{timestamp}.csv'
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Export patients
                cursor.execute('SELECT * FROM patients')
                patients = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(patients)
            
            return filename
        
        elif export_type.lower() == 'json':
            filename = f'hospital_queue_export_{timestamp}.json'
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all data
                cursor.execute('SELECT * FROM patients')
                patients = cursor.fetchall()
                patient_columns = [desc[0] for desc in cursor.description]
                
                cursor.execute('SELECT * FROM queue_history')
                history = cursor.fetchall()
                history_columns = [desc[0] for desc in cursor.description]
                
                data = {
                    'export_time': timestamp,
                    'patients': [
                        dict(zip(patient_columns, row)) for row in patients
                    ],
                    'queue_history': [
                        dict(zip(history_columns, row)) for row in history
                    ]
                }
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            
            return filename
        
        return None
    
    def backup_database(self) -> str:
        """
        Create a backup of the database
        """
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backup_hospital_queue_{timestamp}.db'
        
        shutil.copy2(self.db_name, backup_file)
        return backup_file
    
    def clear_old_records(self, days: int = 30) -> int:
        """
        Clear records older than specified days
        Returns: Number of records deleted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete old patients
            cursor.execute('''
                DELETE FROM patients 
                WHERE registration_time < datetime('now', ?)
                AND status = 'completed'
            ''', (f'-{days} days',))
            
            patients_deleted = cursor.rowcount
            
            # Delete old history
            cursor.execute('''
                DELETE FROM queue_history 
                WHERE action_time < datetime('now', ?)
            ''', (f'-{days} days',))
            
            history_deleted = cursor.rowcount
            
            conn.commit()
            
            return patients_deleted + history_deleted
    
    def reset_database(self) -> bool:
        """
        Reset database (for testing/debugging)
        WARNING: This deletes all data!
        """
        confirm = input("⚠️  WARNING: This will delete ALL data. Type 'CONFIRM' to proceed: ")
        
        if confirm != 'CONFIRM':
            print("Reset cancelled.")
            return False
        
        try:
            # Close any existing connections
            if os.path.exists(self.db_name):
                # Delete the database file
                os.remove(self.db_name)
                print(f"✅ Database file '{self.db_name}' deleted.")
            
            # Reinitialize
            self.init_database()
            print("✅ Database reinitialized successfully.")
            return True
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            return False