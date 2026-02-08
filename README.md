# 🏥 Arogya Mitra - Health Companion App

A comprehensive health management application designed specifically for Indian users, featuring multi-language support, AI-powered prescription analysis, and emergency services.

## ✨ Features

### 🌐 Multi-Language Support
- English, Hindi, Bengali, Odia, Malayalam
- Real-time translation using Google Translate API
- Localized UI and medical terminology

### 👤 User Management
- Registration with required-field validation (name, phone, age, gender, state, city, password)
- State → City smart picker:
  - City options filtered by selected state
  - "Other (type manually)" to enter any city
  - Works inside the registration panel without rerun glitches
- Secure authentication system (hashed passwords)
- User profile management

### 📋 Health Records
- Digital health record storage with required-field checks on add/edit
- Categories: Consultation, Lab Report, Prescription, Vaccination, Surgery, Other
- Doctor name, hospital/clinic, and record date tracked
- Document upload (PDF, JPG/PNG) with in-app preview

### 💊 AI-Powered Prescription Analysis
- OCR-based prescription text extraction
- Medication information parsing
- Dosage and frequency analysis
- Multi-language prescription support

### 🚨 Emergency SOS
- Emergency contact information
- Hospital locator with maps
- City-wise hospital database
- Real-time location-based services

### 📊 Health Dashboard
- Vital signs tracking
- Health score calculation
- Medication reminders
- Achievement system with badges

### ⚙️ Admin Portal
- Full CRUD for Users
  - Create users (admin-side onboarding)
  - Update any user details; optional password reset
  - Delete user with cascade removal of all their data (records, docs, vitals, analyses, badges)
- Full CRUD for Health Records of selected user
  - Add, edit, delete records with validation
- Analytics dashboard: totals, trends, city distribution, common conditions

## 🛠️ Technology Stack

- **Frontend:** Streamlit
- **Backend:** Python
- **Database:** SQLite
- **OCR:** Tesseract
- **Maps:** Folium
- **Charts:** Plotly
- **Translation:** Google Translate API

## 🚀 Installation

### Prerequisites
- Python 3.11+
- Tesseract OCR
- Git

### Setup
1) Clone the repository:
```bash
git clone https://github.com/abhaypratap0709/Arogya-Mitra-Health-Companion.git
cd Arogya-Mitra-Health-Companion
```

2) Create and activate a virtual environment (recommended):
```bash
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

3) Install dependencies:
```bash
pip install -r requirements.txt
```

4) Install Tesseract OCR:
- **Windows:** Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- **Linux:** `sudo apt-get install tesseract-ocr`
- **macOS:** `brew install tesseract`

5) Run the application:
```bash
streamlit run app.py
```

6) (Optional) Launch Admin Portal directly (skips end-user login):
```bash
streamlit run admin_access.py
```

## 🔐 Admin Access

- **Username:** admin
- **Password:** admin123
 
Alternatively, edit `admin_portal.py` to change credentials in `self.admin_credentials`.

## 📱 Usage

1) Registration
   - Fill all required fields; errors show inline and as a banner if anything is missing
   - Choose State, then City (or select "Other (type manually)")
2) Health Records
   - Add records with type, description, doctor, hospital, date
   - Edit/Delete records from Admin portal (user-side edit can be extended similarly)
3) Prescription Analysis
   - Upload JPG/PNG; OCR extracts text and detects medications
   - Results are saved to the database
4) Emergency Services
   - Quick access numbers and nearby hospitals by city
5) Dashboard
   - View health score, badges, recent activity
6) Admin Portal
   - Manage users and their records; run analytics

## 🏥 Emergency Services

The app includes comprehensive emergency services for all major Indian cities:
- Delhi, Mumbai, Bangalore, Chennai, Hyderabad
- Kolkata, Pune, Ahmedabad, Jaipur, Kochi
- Lucknow, Chandigarh, Indore, Bhubaneswar, Guwahati
- And many more...

## 📊 Admin Features

- User Analytics: totals, registration trends (30 days)
- Geographic Distribution: city-wise analysis and charts
- Health Insights: common conditions by state
- User Management: search, filter (state/gender), pagination, full CRUD

## 🗂️ Project Structure

```
AIStudyCoach/
├─ app.py                    # Main Streamlit app (user flows)
├─ admin_access.py           # Shortcut entry for admin portal
├─ admin_portal.py           # Admin dashboard + CRUD
├─ database.py               # SQLite schema and data access layer
├─ health_dashboard.py       # User-facing dashboard utilities
├─ emergency_sos.py          # SOS contacts and hospital locator
├─ ocr_analyzer.py           # Tesseract OCR + parsing
├─ translator.py             # Translation utilities
├─ indian_states_cities.py   # States → Cities data and helpers
├─ utils.py                  # Session/init helpers
├─ arogya_mitra.db           # SQLite DB (created at runtime)
└─ requirements.txt
```

## 🧪 Quick Smoke Test

1) Start the app: `streamlit run app.py`
2) Register a user (pick any state, choose a city suggestion, or manual city)
3) Add a health record (leave a field blank to see validation)
4) Open Admin Portal and edit/delete that record
5) Upload a sample prescription to test OCR

## 🛠️ Troubleshooting

- Missing Tesseract OCR: the Prescription page shows a warning; follow the in-app guide.
- Streamlit callback errors inside forms: ensure only `form_submit_button` has callbacks; this app already avoids forbidden callbacks.
- City list not changing with State: refresh; the city picker keys are namespaced per state to avoid stale session state.
- DB locked on Windows: close any external viewer of `arogya_mitra.db` and retry.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Author

**Abhay Pratap**
- GitHub: [@abhaypratap0709](https://github.com/abhaypratap0709)
- LinkedIn: [abhay-kumar-singh-264513269](https://linkedin.com/in/abhay-kumar-singh-264513269)

## 🙏 Acknowledgments

- Streamlit team for the amazing framework
- Google Translate API for multi-language support
- Tesseract OCR for prescription analysis
- Folium for mapping capabilities
- Plotly for interactive charts



