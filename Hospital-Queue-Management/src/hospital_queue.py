"""
Hospital Queue Management System
Core queue logic and database interface
"""

from database import HospitalDatabase
from datetime import datetime

class HospitalQueueSystem:
    def __init__(self):
        self.db = HospitalDatabase()
        self.current_token = None
    
    def register_patient(self, name, age=None, condition=None, is_emergency=False, is_followup=False, department=None):
        """Register patient using database"""
        priority = 1 if is_emergency else 3 if is_followup else 2
        
        patient_data = {
            'full_name': name,
            'age': age,
            'medical_condition': condition,
            'priority_level': priority,
            'department': department,
            'is_follow_up': is_followup
        }
        
        token = self.db.add_patient(patient_data)
        
        print(f"\n✅ Patient Registered Successfully!")
        print(f"   Name: {name}")
        print(f"   Token: {token}")
        print(f"   Priority: {'🚨 EMERGENCY' if priority == 1 else '🟢 Regular' if priority == 3 else '🔵 Follow-up'}")
        if department:
            print(f"   Department: {department}")
        
        # Store current token for quick operations
        self.current_token = token
        
        return token
    
    def display_current_status(self):
        """Display current queue status"""
        queue = self.db.get_current_queue()
        
        if not queue:
            print("\n📭 No patients in the waiting queue")
            return
        
        print("\n" + "="*60)
        print("🏥 CURRENT HOSPITAL QUEUE STATUS")
        print("="*60)
        
        # Current patient in consultation
        current = self.db.get_current_patient()
        if current:
            token, name, department, doctor, start_time = current
            print(f"\n👨‍⚕️ CURRENTLY CONSULTING:")
            print(f"   Token: {token}")
            print(f"   Name: {name}")
            print(f"   Department: {department}")
            print(f"   Doctor: {doctor}")
            print(f"   Started: {start_time}")
        else:
            print(f"\n👨‍⚕️ CURRENTLY CONSULTING: No patient in consultation")
        
        # Next patient
        next_patient = self.db.get_next_patient()
        if next_patient:
            token, name, department, priority, wait_time, condition = next_patient
            print(f"\n⏭️  NEXT IN LINE:")
            print(f"   Token: {token}")
            print(f"   Name: {name}")
            print(f"   Department: {department}")
            print(f"   Priority: {'🚨 EMERGENCY' if priority == 1 else '🟢 Regular' if priority == 2 else '🔵 Follow-up'}")
            print(f"   Estimated Wait: {wait_time} minutes")
        
        # Queue summary
        stats = self.db.get_average_waiting_count()
        
        print(f"\n📊 QUEUE SUMMARY:")
        print(f"   Currently waiting: {stats['currently_waiting']} patients")
        print(f"   🚨 Emergency cases today: {stats['emergency_cases']}")
        print(f"   🟢 Regular cases today: {stats['regular_cases']}")
        print(f"   🔵 Follow-up cases today: {stats['follow_up_cases']}")
        
        # Department breakdown
        if stats['department_breakdown']:
            print(f"\n🏥 DEPARTMENT BREAKDOWN:")
            for dept, count in stats['department_breakdown']:
                if dept:
                    print(f"   {dept}: {count} waiting")
        
        print("="*60)
    
    def complete_consultation(self, token=None):
        """Complete consultation for a patient"""
        try:
            if token is None:
                # Get the next patient
                next_patient = self.db.get_next_patient()
                if not next_patient:
                    print("❌ No patients waiting for consultation")
                    return False
                
                token = next_patient[0]
            
            # Handle different token formats
            token_str = str(token)
            
            # Complete consultation using database
            success = self.db.complete_consultation(token_str)
            
            if success:
                print(f"\n✅ Consultation completed for token: {token_str}")
            else:
                print(f"❌ Failed to complete consultation. Token may not exist or is not in consultation.")
            
            return success
            
        except Exception as e:
            print(f"❌ Error completing consultation: {e}")
            return False
    
    def view_patient_details(self, token):
        """View details of a specific patient"""
        try:
            # Handle token input
            token_str = str(token)
            
            patient = self.db.get_patient_by_token(token_str)
            
            if patient:
                print("\n" + "="*60)
                print("📋 PATIENT DETAILS")
                print("="*60)
                
                print(f"\nToken: {patient['token_number']}")
                print(f"Name: {patient['full_name']}")
                print(f"Age: {patient['age'] if patient['age'] else 'Not specified'}")
                print(f"Gender: {patient['gender'] if patient['gender'] else 'Not specified'}")
                print(f"Phone: {patient['phone_number'] if patient['phone_number'] else 'Not specified'}")
                print(f"Condition: {patient['medical_condition'] if patient['medical_condition'] else 'Not specified'}")
                print(f"Priority: {patient['priority_text']}")
                print(f"Department: {patient['department'] if patient['department'] else 'General'}")
                print(f"Status: {patient['status'].upper()}")
                print(f"Registered: {patient['registration_time']}")
                print(f"Estimated Wait: {patient['estimated_wait_time']} minutes")
                
                if patient['doctor_assigned']:
                    print(f"Doctor Assigned: {patient['doctor_assigned']}")
                
                if patient['consultation_start_time']:
                    print(f"Consultation Started: {patient['consultation_start_time']}")
                
                if patient['consultation_end_time']:
                    print(f"Consultation Ended: {patient['consultation_end_time']}")
                
                print("="*60)
            else:
                print(f"❌ No patient found with token: {token_str}")
                
        except Exception as e:
            print(f"❌ Error viewing patient details: {e}")
    
    def get_statistics(self):
        """Display comprehensive statistics"""
        stats = self.db.get_average_waiting_count()
        
        print("\n" + "="*60)
        print("📈 HOSPITAL QUEUE STATISTICS")
        print("="*60)
        
        print(f"\n📊 Last 24 Hours:")
        print(f"   Total patients: {stats['total_patients_last_24h']}")
        print(f"   Average wait time: {stats['average_wait_time']} minutes")
        print(f"   Maximum wait time: {stats['max_wait_time']} minutes")
        print(f"   Minimum wait time: {stats['min_wait_time']} minutes")
        
        print(f"\n🚦 Case Distribution:")
        print(f"   Emergency cases: {stats['emergency_cases']}")
        print(f"   Regular cases: {stats['regular_cases']}")
        print(f"   Follow-up cases: {stats['follow_up_cases']}")
        
        print(f"\n📈 Current Status:")
        print(f"   Patients currently waiting: {stats['currently_waiting']}")
        
        # Show available doctors
        doctors = self.db.get_available_doctors()
        if doctors:
            print(f"\n👨‍⚕️ Available Doctors:")
            for doctor, specialization, department in doctors:
                print(f"   {doctor} ({specialization}) - {department}")
        
        print("="*60)
    
    def register_emergency_patient(self, name, condition=None, department="Emergency"):
        """Register an emergency patient"""
        return self.register_patient(
            name=name,
            condition=condition,
            is_emergency=True,
            department=department
        )
    
    def register_followup_patient(self, name, department=None):
        """Register a follow-up patient"""
        return self.register_patient(
            name=name,
            is_followup=True,
            department=department
        )
    
    def view_queue_history(self, token=None):
        """View queue history for a patient or all"""
        try:
            history = self.db.get_queue_history(token)
            
            if not history:
                print("\n📭 No history found")
                return
            
            print("\n" + "="*60)
            print("📜 QUEUE HISTORY")
            print("="*60)
            
            for record in history:
                if len(record) >= 9:
                    action_time, action, prev_status, new_status, pos_before, pos_after, performed_by, patient_name, *extra = record
                    token_num = extra[0] if extra else (token if token else "N/A")
                else:
                    action_time, action, prev_status, new_status, pos_before, pos_after, performed_by, patient_name = record
                    token_num = token if token else "N/A"
                
                print(f"\nTime: {action_time}")
                print(f"Action: {action}")
                print(f"Token: {token_num}")
                print(f"Patient: {patient_name}")
                print(f"Status: {prev_status} → {new_status}")
                if pos_before:
                    print(f"Queue Position: {pos_before} → {pos_after if pos_after else 'N/A'}")
                print(f"Performed by: {performed_by}")
            
            print("="*60)
            
        except Exception as e:
            print(f"❌ Error viewing history: {e}")
    
    def show_departments(self):
        """Show all departments"""
        departments = self.db.get_departments()
        
        print("\n" + "="*60)
        print("🏥 HOSPITAL DEPARTMENTS")
        print("="*60)
        
        for dept_name, dept_code, wait_time, active_docs in departments:
            print(f"\n{dept_name} ({dept_code})")
            print(f"   Current wait time: {wait_time} minutes")
            print(f"   Active doctors: {active_docs}")
        
        print("="*60)
    
    def start_consultation(self, token, doctor_name=None):
        """Start consultation for a patient"""
        try:
            token_str = str(token)
            success = self.db.start_consultation(token_str, doctor_name)
            
            if success:
                print(f"\n✅ Consultation started for token: {token_str}")
                if doctor_name:
                    print(f"   Doctor assigned: {doctor_name}")
            else:
                print(f"❌ Failed to start consultation. Patient may not exist or is not waiting.")
            
            return success
            
        except Exception as e:
            print(f"❌ Error starting consultation: {e}")
            return False