# 🏥 Hospital Queue Management System

## 👥 Team DACOITS (Team 5)
**Team Members:**
- CHINTHA SANDEEP ABHILASH (99230040286) - Lead Developer
- ALLAM HARSHA VARDHAN (99230040253) - Database Architect
- DAREDDY BHARGAV REDDY (99230040289) - Queue Algorithm Specialist
- CHAPPIDI JASWANTH REDDY (99230040277) - UI/UX Designer
- GUPI HARI KRISHNA (99230040314) - Testing & Documentation

## 📋 Problem Statement #3
Hospitals often suffer from long waiting times due to poor queue handling. Create a queue management program for hospital patients.

**Requirements:**
- Register patients with token numbers
- Assign priority for emergency cases
- Display current and next patient
- Remove patients after consultation
- Show average waiting count

## 🚀 Features Implemented

### Core Features
✅ **Priority Queue Management** - Emergency cases get immediate attention  
✅ **Smart Token System** - Unique DEPT-DATE-SEQ tokens (e.g., ER-20250120-001)  
✅ **Real-time Status Display** - Current and next patient visibility  
✅ **Consultation Tracking** - Complete patient lifecycle management  
✅ **Statistical Analytics** - Average wait times, patient counts, department loads  

### Advanced Features
✅ **Department-wise Management** - Multiple hospital departments  
✅ **Doctor Assignment** - Track doctor availability and assignments  
✅ **Complete Audit Trail** - History of all queue movements  
✅ **Data Export** - CSV/JSON export functionality  
✅ **Database Backup** - Automatic backup system  
✅ **Wait Time Estimation** - Real-time wait predictions  

## 🛠️ Technology Stack

- **Programming Language**: Python 3.8+
- **Database**: SQLite (Lightweight, file-based)
- **Architecture**: Modular OOP Design
- **Dependencies**: Zero external dependencies (pure Python)

## 📁 Project Structure
hospital-queue-management/
├── src/
│ ├── database.py # Database operations and schema
│ ├── hospital_queue.py # Core queue logic and algorithms
│ └── main.py # User interface and main application
├── requirements.txt # Python dependencies
└── README.md # Project documentation


## 🔧 Installation & Usage

### Prerequisites
- Python 3.8 or higher
- Git (for cloning repository)

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sandy5604G/hospital-queue-management
   cd hospital-queue-management

   # Navigate to src directory
cd src

# Run main application
python main.py
