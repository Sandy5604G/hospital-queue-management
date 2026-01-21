"""
Main Hospital Queue Management System Application
"""

from hospital_queue import HospitalQueueSystem
import sys

def display_menu():
    """Display the main menu"""
    print("\n" + "="*60)
    print("HOSPITAL QUEUE MANAGEMENT SYSTEM")
    print("="*60)
    print("\n1. Register New Patient")
    print("2. View Current Queue Status")
    print("3. Complete Consultation")
    print("4. View Patient Details")
    print("5. View Statistics")
    print("6. Register Emergency Patient")
    print("7. Register Follow-up Patient")
    print("8. View Departments")
    print("9. View Queue History")
    print("10. Clear All Records")
    print("11. Backup Database")
    print("12. Export Data")
    print("13. Exit")
    print("="*60)

def main():
    system = HospitalQueueSystem()
    
    while True:
        display_menu()
        
        try:
            choice = input("\nEnter your choice (1-13): ").strip()
            
            if choice == '1':
                # Register regular patient
                print("\nREGISTER NEW PATIENT")
                print("-"*40)
                name = input("Enter patient name: ").strip()
                age = input("Enter age (optional): ").strip()
                condition = input("Enter condition/description (optional): ").strip()
                department = input("Enter department (optional, press Enter for General): ").strip()
                
                age_int = int(age) if age.isdigit() else None
                department = department if department else "General Medicine"
                
                system.register_patient(
                    name=name,
                    age=age_int,
                    condition=condition,
                    is_emergency=False,
                    is_followup=False,
                    department=department
                )
            
            elif choice == '2':
                # View current status
                system.display_current_status()
            
            elif choice == '3':
                # Complete consultation
                print("\nCOMPLETE CONSULTATION")
                print("-"*40)
                token_input = input("Enter token number (or press Enter for next patient): ").strip()
                
                if token_input:
                    system.complete_consultation(token_input)
                else:
                    system.complete_consultation()
            
            elif choice == '4':
                # View patient details
                print("\nVIEW PATIENT DETAILS")
                print("-"*40)
                token_input = input("Enter token number: ").strip()
                
                if token_input:
                    system.view_patient_details(token_input)
                else:
                    print("Please enter a token number")
            
            elif choice == '5':
                # View statistics
                system.get_statistics()
            
            elif choice == '6':
                # Register emergency patient
                print("\nREGISTER EMERGENCY PATIENT")
                print("-"*40)
                name = input("Enter patient name: ").strip()
                condition = input("Enter emergency condition: ").strip()
                
                system.register_emergency_patient(
                    name=name,
                    condition=condition
                )
            
            elif choice == '7':
                # Register follow-up patient
                print("\nREGISTER FOLLOW-UP PATIENT")
                print("-"*40)
                name = input("Enter patient name: ").strip()
                department = input("Enter department (optional): ").strip()
                
                department = department if department else None
                
                system.register_followup_patient(
                    name=name,
                    department=department
                )
            
            elif choice == '8':
                # View departments
                system.show_departments()
            
            elif choice == '9':
                # View queue history
                print("\nVIEW QUEUE HISTORY")
                print("-"*40)
                token_input = input("Enter token number (or press Enter for all history): ").strip()
                
                if token_input:
                    system.view_queue_history(token_input)
                else:
                    system.view_queue_history()
            
            elif choice == '10':
                # Clear all records
                print("\nCLEAR ALL RECORDS")
                print("-"*40)
                confirm = input("WARNING: This will reset the database. Type 'YES' to confirm: ").strip()
                
                if confirm.upper() == 'YES':
                    success = system.db.reset_database()
                    if success:
                        system = HospitalQueueSystem()  # Reinitialize
                else:
                    print("Operation cancelled.")
            
            elif choice == '11':
                # Backup database
                print("\nBACKUP DATABASE")
                print("-"*40)
                backup_file = system.db.backup_database()
                print(f"Database backed up to: {backup_file}")
            
            elif choice == '12':
                # Export data
                print("\nEXPORT DATA")
                print("-"*40)
                export_type = input("Export as (csv/json): ").strip().lower()
                
                if export_type in ['csv', 'json']:
                    export_file = system.db.export_data(export_type)
                    print(f"Data exported to: {export_file}")
                else:
                    print("Invalid export type. Use 'csv' or 'json'.")
            
            elif choice == '13':
                # Exit
                print("\nThank you for using Hospital Queue Management System!")
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please enter a number between 1-13.")
        
        except ValueError:
            print("Invalid input. Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\nOperation interrupted by user.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
        
        # Only pause if not exiting
        if choice != '13':
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    # ASCII Art Banner (without Unicode)
    print(r"""
     _    _           _           _   _____                    _            
    | |  | |         | |         | | |  __ \                  | |           
    | |__| | ___  ___| |_ _   _  | | | |  \/_   _  ___  ___   | | ___ _   _ 
    |  __  |/ _ \/ __| __| | | | | | | | __| | | |/ _ \/ __|  | |/ _ \ | | |
    | |  | | (_) \__ \ |_| |_| | | | | |_\ \ |_| |  __/\__ \  | |  __/ |_| |
    |_|  |_|\___/|___/\__|\__, | |_|  \____/\__,_|\___||___/  |_|\___|\__, |
                           __/ |                                       __/ |
                          |___/                                       |___/ 
    """)
    print("Hospital Queue Management System v2.0")
    print("Team DACOITS - Team 5\n")
    
    main()