import streamlit as st
import pandas as pd
from PIL import Image
import io
import base64

# Import custom modules
from database import DatabaseManager
from ocr_analyzer import PrescriptionAnalyzer
from translator import TranslationManager
from emergency_sos import EmergencySOSManager
from health_dashboard import HealthDashboard
from utils import init_session_state, get_language_options
from indian_states_cities import get_states, get_cities_for_state
from admin_portal import AdminPortal

st.set_page_config(
    page_title="Arogya Mitra - Health Companion",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state (must be after set_page_config)
init_session_state()

# Initialize managers
db_manager = DatabaseManager()
ocr_analyzer = PrescriptionAnalyzer()
translator = TranslationManager()
sos_manager = EmergencySOSManager()
dashboard = HealthDashboard(db_manager)
admin_portal = AdminPortal()

def main():
    # Add loading spinner
    with st.spinner("Loading Arogya Mitra..."):
        # Language selection in sidebar
        st.sidebar.title("🌐 Language / भाषा")
        language_options = get_language_options()
        selected_language = st.sidebar.selectbox(
            "Select Language",
            options=list(language_options.keys()),
            index=0
        )
        st.session_state.language = language_options[selected_language]
        
        # Translate main title
        main_title = translator.translate_text("Arogya Mitra - Your Health Companion", st.session_state.language)
        st.title(f"🏥 {main_title}")
        
        # Add app description
        st.markdown("""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3 style="color: #1f77b4; margin-top: 0;">🌟 Your Complete Health Management Solution</h3>
            <p style="margin-bottom: 0;">Manage your health records, get AI-powered prescription analysis, access emergency services, 
            and chat with our health bot - all in multiple Indian languages!</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Navigation
    nav_options = {
        "Dashboard": "📊 Dashboard",
        "Health Records": "📋 Health Records", 
        "Upload Documents": "📤 Upload Documents",
        "Prescription Analysis": "💊 Prescription Analysis",
        "Health Chatbot": "🤖 Health Chatbot",
        "Emergency SOS": "🚨 Emergency SOS",
        "Profile": "👤 Profile",
        "Admin Portal": "⚙️ Admin Portal"
    }
    
    # Translate navigation options
    translated_nav = {}
    for key, value in nav_options.items():
        translated_nav[key] = translator.translate_text(value, st.session_state.language)
    
    selected_page = st.sidebar.radio(
        translator.translate_text("Navigation", st.session_state.language),
        options=list(translated_nav.keys()),
        format_func=lambda x: translated_nav[x]
    )
    
    # Check if admin portal is selected
    if selected_page == "Admin Portal":
        show_admin_portal()
    else:
        # User registration/login
        if 'user_id' not in st.session_state:
            show_registration_login()
        else:
            # Show selected page
            if selected_page == "Dashboard":
                show_dashboard()
            elif selected_page == "Health Records":
                show_health_records()
            elif selected_page == "Upload Documents":
                show_upload_documents()
            elif selected_page == "Prescription Analysis":
                show_prescription_analysis()
            elif selected_page == "Health Chatbot":
                show_health_chatbot()
            elif selected_page == "Emergency SOS":
                show_emergency_sos()
            elif selected_page == "Profile":
                show_profile()

def show_registration_login():
    st.subheader(translator.translate_text("Welcome to Arogya Mitra", st.session_state.language))
    
    tab1, tab2 = st.tabs([
        translator.translate_text("Login", st.session_state.language),
        translator.translate_text("Register", st.session_state.language)
    ])
    
    with tab1:
        with st.form("login_form"):
            phone = st.text_input(translator.translate_text("Phone Number", st.session_state.language))
            password = st.text_input(translator.translate_text("Password", st.session_state.language), type="password")
            submitted = st.form_submit_button(translator.translate_text("Login", st.session_state.language))
            
            if submitted and phone and password:
                user = db_manager.authenticate_user(phone, password)
                if user:
                    st.session_state.user_id = user[0]
                    st.session_state.user_name = user[1]
                    st.success(translator.translate_text("Login successful!", st.session_state.language))
                    st.rerun()
                else:
                    st.error(translator.translate_text("Invalid credentials", st.session_state.language))
    
    with tab2:
        with st.container(border=True):
            # Interactive state/city controls (rendered in same visual box as the form)
            col_state_city_1, col_state_city_2 = st.columns(2)
            with col_state_city_1:
                states = get_states()
                state_value = st.selectbox(
                    translator.translate_text("State", st.session_state.language),
                    options=states,
                    key="reg_state"
                )
            with col_state_city_2:
                state_cities = get_cities_for_state(state_value)
                city_options = ["-"] + state_cities + ["Other (type manually)"]
                city_key = f"reg_city_select_{state_value}"
                manual_key = f"reg_city_manual_{state_value}"
                city_select_value = st.selectbox(
                    translator.translate_text("City", st.session_state.language),
                    options=city_options,
                    index=0 if city_key not in st.session_state or st.session_state.get(city_key) not in city_options else city_options.index(st.session_state.get(city_key)),
                    key=city_key
                )
                if city_select_value == "Other (type manually)":
                    _ = st.text_input(
                        translator.translate_text("Enter city manually", st.session_state.language),
                        value=st.session_state.get(manual_key, ""),
                        key=manual_key
                    )

            # Registration form
            with st.form("register_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input(translator.translate_text("Full Name", st.session_state.language))
                    phone = st.text_input(translator.translate_text("Phone Number", st.session_state.language))
                    age = st.number_input(translator.translate_text("Age", st.session_state.language), min_value=1, max_value=100)
                    gender = st.selectbox(translator.translate_text("Gender", st.session_state.language), 
                                        ["Male", "Female", "Other"])
                
                with col2:
                    password = st.text_input(translator.translate_text("Password", st.session_state.language), type="password")
                
                submitted = st.form_submit_button(translator.translate_text("Register", st.session_state.language))
                
                # Determine final state and city from session
                selected_state = st.session_state.get("reg_state")
                city_key = f"reg_city_select_{selected_state}"
                manual_key = f"reg_city_manual_{selected_state}"
                sel = st.session_state.get(city_key, "-")
                if sel == "Other (type manually)":
                    final_city = (st.session_state.get(manual_key, "") or "").strip() or None
                else:
                    final_city = None if (sel is None or sel == "-") else sel

                if submitted and all([name, phone, age, gender, password, selected_state, final_city]):
                    user_id = db_manager.create_user(name, phone, age, gender, password, selected_state, final_city)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.user_name = name
                        st.success(translator.translate_text("Registration successful!", st.session_state.language))
                        st.rerun()
                    else:
                        st.error(translator.translate_text("Registration failed. Phone number may already exist.", st.session_state.language))
                elif submitted:
                    st.error(translator.translate_text("Please fill all required fields (including City).", st.session_state.language))

def show_dashboard():
    st.subheader(translator.translate_text("Health Dashboard", st.session_state.language))
    dashboard.render_dashboard(st.session_state.user_id, st.session_state.language)

def show_health_records():
    st.subheader(translator.translate_text("Health Records", st.session_state.language))
    
    # Display health records
    records = db_manager.get_health_records(st.session_state.user_id)
    
    if records:
        df = pd.DataFrame(records)
        df.columns = ['ID', 'Date', 'Type', 'Description', 'Doctor', 'Hospital']
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        st.dataframe(df, use_container_width=True)
    else:
        st.info(translator.translate_text("No health records found. Upload documents to get started.", st.session_state.language))
    
    # Add new health record
    with st.expander(translator.translate_text("Add New Health Record", st.session_state.language)):
        # Surface any prior validation errors (persisted through reruns)
        if st.session_state.get("health_record_form_error"):
            st.error(st.session_state["health_record_form_error"])

        with st.form("health_record_form"):
            record_type = st.selectbox(
                translator.translate_text("Record Type", st.session_state.language) + " *",
                ["Consultation", "Lab Report", "Prescription", "Vaccination", "Surgery", "Other"]
            )
            description = st.text_area(translator.translate_text("Description", st.session_state.language) + " *")
            # Inline field errors from previous submit
            if st.session_state.get("health_record_field_errors", {}).get("description"):
                st.caption(":red[" + translator.translate_text("Description is required", st.session_state.language) + "]")

            doctor_name = st.text_input(translator.translate_text("Doctor Name", st.session_state.language) + " *")
            if st.session_state.get("health_record_field_errors", {}).get("doctor_name"):
                st.caption(":red[" + translator.translate_text("Doctor name is required", st.session_state.language) + "]")

            hospital_name = st.text_input(translator.translate_text("Hospital/Clinic Name", st.session_state.language) + " *")
            if st.session_state.get("health_record_field_errors", {}).get("hospital_name"):
                st.caption(":red[" + translator.translate_text("Hospital/Clinic name is required", st.session_state.language) + "]")

            record_date = st.date_input(translator.translate_text("Date", st.session_state.language) + " *")
            if st.session_state.get("health_record_field_errors", {}).get("record_date"):
                st.caption(":red[" + translator.translate_text("Date is required", st.session_state.language) + "]")
            
            submitted = st.form_submit_button(translator.translate_text("Add Record", st.session_state.language))
            
            if submitted:
                missing_fields = []
                # record_type comes from selectbox, but keep check for completeness
                if not record_type:
                    missing_fields.append(translator.translate_text("Record Type", st.session_state.language))
                if not description or not str(description).strip():
                    missing_fields.append(translator.translate_text("Description", st.session_state.language))
                if not doctor_name or not doctor_name.strip():
                    missing_fields.append(translator.translate_text("Doctor Name", st.session_state.language))
                if not hospital_name or not hospital_name.strip():
                    missing_fields.append(translator.translate_text("Hospital/Clinic Name", st.session_state.language))
                if not record_date:
                    missing_fields.append(translator.translate_text("Date", st.session_state.language))

                if missing_fields:
                    st.session_state["health_record_form_error"] = (
                        translator.translate_text("Please fill all required fields:", st.session_state.language)
                        + " " + ", ".join(missing_fields)
                    )
                    st.session_state["health_record_field_errors"] = {
                        "description": (not description or not str(description).strip()),
                        "doctor_name": (not doctor_name or not doctor_name.strip()),
                        "hospital_name": (not hospital_name or not hospital_name.strip()),
                        "record_date": (not record_date),
                    }
                else:
                    # Clear any previous error
                    if st.session_state.get("health_record_form_error"):
                        del st.session_state["health_record_form_error"]
                    if st.session_state.get("health_record_field_errors"):
                        del st.session_state["health_record_field_errors"]
                    db_manager.add_health_record(
                        st.session_state.user_id, record_type, description,
                        doctor_name, hospital_name, record_date
                    )
                    st.success(translator.translate_text("Health record added successfully!", st.session_state.language))
                    st.rerun()

def show_upload_documents():
    st.subheader(translator.translate_text("Upload Medical Documents", st.session_state.language))
    
    uploaded_files = st.file_uploader(
        translator.translate_text("Choose medical documents", st.session_state.language),
        type=['pdf', 'jpg', 'jpeg', 'png'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"📄 {uploaded_file.name}")
                
                # Show image preview for image files
                if uploaded_file.type.startswith('image'):
                    image = Image.open(uploaded_file)
                    st.image(image, width=300)
            
            with col2:
                document_type = st.selectbox(
                    translator.translate_text("Document Type", st.session_state.language),
                    ["Prescription", "Lab Report", "X-Ray", "Scan", "Vaccination Card", "Other"],
                    key=f"type_{uploaded_file.name}"
                )
                
                if st.button(translator.translate_text("Save Document", st.session_state.language), key=f"save_{uploaded_file.name}"):
                    # Convert file to bytes for storage
                    file_bytes = uploaded_file.getvalue()
                    file_base64 = base64.b64encode(file_bytes).decode()
                    
                    # Save to database
                    db_manager.save_document(
                        st.session_state.user_id,
                        uploaded_file.name,
                        document_type,
                        file_base64,
                        uploaded_file.type
                    )
                    st.success(translator.translate_text("Document saved successfully!", st.session_state.language))
    
    # Display saved documents
    st.subheader(translator.translate_text("Saved Documents", st.session_state.language))
    documents = db_manager.get_user_documents(st.session_state.user_id)
    
    if documents:
        for doc in documents:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📄 {doc[1]} ({doc[2]})")
                st.caption(f"Uploaded: {doc[4]}")
            with col2:
                if doc[5].startswith('image'):
                    if st.button("View", key=f"view_{doc[0]}"):
                        # Decode and display image
                        image_bytes = base64.b64decode(doc[3])
                        image = Image.open(io.BytesIO(image_bytes))
                        st.image(image, caption=doc[1])
            with col3:
                if st.button("Delete", key=f"delete_{doc[0]}"):
                    db_manager.delete_document(doc[0])
                    st.success(translator.translate_text("Document deleted!", st.session_state.language))
                    st.rerun()

def show_prescription_analysis():
    st.subheader(translator.translate_text("AI-Powered Prescription Analysis", st.session_state.language))
    
    # Tesseract status check
    tesseract_ok = False
    try:
        import pytesseract
        _ = pytesseract.get_tesseract_version()
        tesseract_ok = True
    except Exception as e:
        st.warning(translator.translate_text("Tesseract OCR is not installed or not found. Please install it to enable analysis.", st.session_state.language))
        st.caption("Windows: Install from https://github.com/UB-Mannheim/tesseract/wiki and restart the app.")
        
        # Show installation guide
        with st.expander("📋 Installation Guide"):
            st.markdown("""
            **For Windows:**
            1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
            2. Install the downloaded .exe file
            3. Add Tesseract to your system PATH
            4. Restart the application
            
            **For Linux:**
            ```bash
            sudo apt-get install tesseract-ocr
            ```
            
            **For macOS:**
            ```bash
            brew install tesseract
            ```
            """)
    
    uploaded_file = st.file_uploader(
        translator.translate_text("Upload prescription image", st.session_state.language),
        type=['jpg', 'jpeg', 'png']
    )
    
    if uploaded_file and tesseract_ok:
        image = Image.open(uploaded_file)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(image, caption=translator.translate_text("Uploaded Prescription", st.session_state.language))
        
        with col2:
            if st.button(translator.translate_text("Analyze Prescription", st.session_state.language)):
                try:
                    with st.spinner(translator.translate_text("Analyzing prescription...", st.session_state.language)):
                        # Perform OCR analysis
                        analysis_result = ocr_analyzer.analyze_prescription(image, st.session_state.language)
                        
                        if analysis_result:
                            st.success(translator.translate_text("Analysis Complete!", st.session_state.language))
                            
                            # Display extracted text
                            st.subheader(translator.translate_text("Extracted Text:", st.session_state.language))
                            st.text_area("", analysis_result['extracted_text'], height=100, disabled=True)
                            
                            # Display medication analysis
                            if analysis_result['medications']:
                                st.subheader(translator.translate_text("Medications Found:", st.session_state.language))
                                for med in analysis_result['medications']:
                                    with st.expander(f"💊 {med['name']}"):
                                        if med['dosage']:
                                            st.write(f"**{translator.translate_text('Dosage', st.session_state.language)}:** {med['dosage']}")
                                        if med['frequency']:
                                            st.write(f"**{translator.translate_text('Frequency', st.session_state.language)}:** {med['frequency']}")
                                        if med['duration']:
                                            st.write(f"**{translator.translate_text('Duration', st.session_state.language)}:** {med['duration']}")
                                        if med['instructions']:
                                            st.write(f"**{translator.translate_text('Instructions', st.session_state.language)}:** {med['instructions']}")
                            
                            # Save analysis to database
                            try:
                                db_manager.save_prescription_analysis(
                                    st.session_state.user_id,
                                    uploaded_file.name,
                                    analysis_result['extracted_text'],
                                    str(analysis_result['medications'])
                                )
                                st.info(translator.translate_text("Analysis saved to your health records!", st.session_state.language))
                            except Exception as e:
                                st.warning(f"Analysis completed but couldn't save to database: {str(e)}")
                        else:
                            st.error(translator.translate_text("Could not analyze prescription. Please ensure the image is clear and try again.", st.session_state.language))
                            st.info(translator.translate_text("Tips for better results: Use good lighting, ensure text is readable, avoid blurry images.", st.session_state.language))
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
                    st.info(translator.translate_text("Please try again or contact support if the problem persists.", st.session_state.language))

def show_emergency_sos():
    st.subheader(translator.translate_text("🚨 Emergency SOS", st.session_state.language))
    
    # Emergency button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚨 EMERGENCY", key="emergency_button", help=translator.translate_text("Click for emergency help", st.session_state.language)):
            st.session_state.emergency_activated = True
    
    if st.session_state.get('emergency_activated', False):
        st.error(translator.translate_text("⚠️ EMERGENCY MODE ACTIVATED", st.session_state.language))
        
        # Emergency contacts
        st.subheader(translator.translate_text("Emergency Contacts", st.session_state.language))
        
        emergency_contacts = [
            {"name": "National Emergency (India)", "number": "112"},
            {"name": "Ambulance", "number": "108"},
            {"name": "Fire Emergency", "number": "101"},
            {"name": "Police", "number": "100"}
        ]
        
        for contact in emergency_contacts:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📞 {contact['name']}: **{contact['number']}**")
            with col2:
                st.markdown(f"[Call Now](tel:{contact['number']})")
        
        # Hospital locator
        st.subheader(translator.translate_text("Nearest Hospitals", st.session_state.language))
        
        # City selection with autocomplete
        available_cities = sos_manager.get_available_cities()
        city_options = [city.title() for city in available_cities]
        
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_city = st.selectbox(
                translator.translate_text("Select your city", st.session_state.language),
                options=city_options,
                index=0
            )
        with col2:
            custom_city = st.text_input(
                translator.translate_text("Or enter custom city", st.session_state.language),
                placeholder="e.g., Mumbai, Delhi, Bangalore"
            )
        
        # Use custom input if provided, otherwise use selected city
        city = custom_city if custom_city else selected_city
        
        if city:
            # Generate and display map
            hospital_map = sos_manager.get_nearest_hospitals_map(city)
            if hospital_map:
                import streamlit.components.v1 as components
                components.html(hospital_map._repr_html_(), height=400)
            
            # Display hospital list
            hospitals = sos_manager.get_hospital_list(city)
            for hospital in hospitals:
                st.write(f"🏥 {hospital}")
        
        # Reset emergency mode
        if st.button(translator.translate_text("Reset Emergency Mode", st.session_state.language)):
            st.session_state.emergency_activated = False
            st.rerun()

def show_profile():
    st.subheader(translator.translate_text("User Profile", st.session_state.language))
    
    # Get user data
    user_data = db_manager.get_user_profile(st.session_state.user_id)
    
    if user_data:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write(f"**{translator.translate_text('Name', st.session_state.language)}:** {user_data[1]}")
            st.write(f"**{translator.translate_text('Phone', st.session_state.language)}:** {user_data[2]}")
            st.write(f"**{translator.translate_text('Age', st.session_state.language)}:** {user_data[3]}")
            st.write(f"**{translator.translate_text('Gender', st.session_state.language)}:** {user_data[4]}")
            if user_data[5]:  # State
                st.write(f"**{translator.translate_text('State', st.session_state.language)}:** {user_data[5]}")
            if user_data[6]:  # City
                st.write(f"**{translator.translate_text('City', st.session_state.language)}:** {user_data[6]}")
        
        with col2:
            # Health score and gamification
            health_score = dashboard.calculate_health_score(st.session_state.user_id)
            st.metric(translator.translate_text("Health Score", st.session_state.language), f"{health_score}/100")
            
            # Display badges
            badges = db_manager.get_user_badges(st.session_state.user_id)
            if badges:
                st.write(f"**{translator.translate_text('Badges Earned', st.session_state.language)}:**")
                for badge in badges:
                    st.write(f"🏆 {badge}")
    
    # Logout button
    if st.button(translator.translate_text("Logout", st.session_state.language)):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def show_health_chatbot():
    """Show health chatbot"""
    try:
        from health_chatbot import main as chatbot_main
        chatbot_main()
    except Exception as e:
        st.error(f"Error loading health chatbot: {str(e)}")
        st.info("Please ensure all dependencies are installed correctly.")

def show_admin_portal():
    """Show admin portal"""
    admin_portal.render_admin_portal()

def add_footer():
    """Add footer to the app"""
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p><strong>🏥 Arogya Mitra</strong> - Your Health Companion</p>
        <p>Made with ❤️ for Indian healthcare | 
        <a href="https://github.com/abhaypratap0709" target="_blank">GitHub</a> | 
        <a href="https://linkedin.com/in/abhay-kumar-singh-264513269" target="_blank">LinkedIn</a></p>
        <p><small>⚠️ This app provides general health information only. Always consult a qualified healthcare provider for medical advice.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
        add_footer()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page or contact support if the problem persists.")
        st.stop()
