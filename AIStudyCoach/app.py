import streamlit as st
try:
    import pandas as pd  # optional
except Exception:
    pd = None  # fallback when pandas is not installed
try:
    from PIL import Image  # optional
except Exception:
    Image = None
import io
import base64
import re

# Import custom modules
from db_router import get_db_manager
from ocr_analyzer import PrescriptionAnalyzer
from translator import TranslationManager
from emergency_sos import EmergencySOSManager
from health_dashboard import HealthDashboard
from utils import init_session_state, get_language_options
from indian_states_cities import get_states, get_cities_for_state
from admin_portal import AdminPortal
try:
    from risk_scoring import score_worker
except Exception:
    score_worker = None
try:
    from speech_notes import SpeechNotesManager
except Exception:
    SpeechNotesManager = None
try:
    from summarizer import ClinicalNoteSummarizer
except Exception:
    ClinicalNoteSummarizer = None
try:
    from jiwer import wer as compute_wer
except Exception:
    compute_wer = None

st.set_page_config(
    page_title="Arogya Mitra - Health Companion",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state (must be after set_page_config)
init_session_state()

# Initialize managers
db_manager = get_db_manager()
ocr_analyzer = PrescriptionAnalyzer()
translator = TranslationManager()
sos_manager = EmergencySOSManager()
dashboard = HealthDashboard(db_manager)
admin_portal = AdminPortal()
speech_notes_manager = SpeechNotesManager() if SpeechNotesManager else None
summarizer_manager = ClinicalNoteSummarizer() if ClinicalNoteSummarizer else None

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
    
    # Sidebar: Admin login gate (hide Admin Portal unless admin is logged in)
    with st.sidebar.expander("Admin", expanded=False):
        if not st.session_state.get("admin_logged_in", False):
            a_user = st.text_input("Admin Username", key="_adm_user")
            a_pass = st.text_input("Admin Password", type="password", key="_adm_pass")
            if st.button("Login as Admin", key="_adm_login_btn"):
                try:
                    if admin_portal.authenticate_admin(a_user, a_pass):
                        st.session_state.admin_logged_in = True
                        st.session_state.admin_username = a_user
                        st.success("Admin login successful")
                        st.rerun()
                    else:
                        st.error("Invalid admin credentials")
                except Exception as _e:
                    st.error("Admin auth error")
        else:
            st.write(f"Logged in as: {st.session_state.get('admin_username','admin')}")
            if st.button("Logout Admin", key="_adm_logout_btn"):
                for k in ["admin_logged_in","admin_username"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.success("Logged out")
                st.rerun()

    # Navigation
    nav_options = {
        "Dashboard": "📊 Dashboard",
        "Health Records": "📋 Health Records", 
        "Upload Documents": "📤 Upload Documents",
        "Prescription Analysis": "💊 Prescription Analysis",
        "Worker Intake": "🛂 Worker Intake",
        "QR Tools": "🔳 QR Tools",
        "Health Chatbot": "🤖 Health Chatbot",
        "Emergency SOS": "🚨 Emergency SOS",
        "Clinical Notes": "🩺 Clinical Notes",
        "Profile": "👤 Profile",
    }
    # Only show Admin Portal when an admin is logged in
    if st.session_state.get("admin_logged_in", False):
        nav_options["Admin Portal"] = "⚙️ Admin Portal"
    
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
            elif selected_page == "Worker Intake":
                show_worker_intake()
            elif selected_page == "QR Tools":
                show_qr_tools()
            elif selected_page == "Health Chatbot":
                show_health_chatbot()
            elif selected_page == "Emergency SOS":
                show_emergency_sos()
            elif selected_page == "Clinical Notes":
                show_clinical_notes()
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
                try:
                    phone_clean = re.sub(r'[\s\-\(\)]', '', phone)  # Clean phone number
                    user = db_manager.authenticate_user(phone_clean, password)
                    if user:
                        st.session_state.user_id = user[0]
                        st.session_state.user_name = user[1]
                        st.success(translator.translate_text("Login successful!", st.session_state.language))
                        st.rerun()
                    else:
                        st.error(translator.translate_text("Invalid credentials", st.session_state.language))
                except Exception as e:
                    st.error(translator.translate_text(f"Login failed: {str(e)}", st.session_state.language))
    
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
                    # Password strength indicator
                    if password:
                        strength = 0
                        strength_text = ""
                        if len(password) >= 8:
                            strength += 1
                        if re.search(r'[A-Z]', password):
                            strength += 1
                        if re.search(r'[a-z]', password):
                            strength += 1
                        if re.search(r'\d', password):
                            strength += 1
                        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                            strength += 1
                        
                        if strength <= 2:
                            strength_text = "🔴 Weak"
                            st.caption(f":red[{strength_text}]")
                        elif strength == 3:
                            strength_text = "🟡 Medium"
                            st.caption(f":orange[{strength_text}]")
                        else:
                            strength_text = "🟢 Strong"
                            st.caption(f":green[{strength_text}]")
                
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

                if submitted:
                    # Validate phone number
                    phone_clean = re.sub(r'[\s\-\(\)]', '', phone)  # Remove spaces, dashes, parentheses
                    phone_pattern = r'^[6-9]\d{9}$'  # Indian mobile number pattern
                    
                    if not all([name, phone, age, gender, password, selected_state, final_city]):
                        st.error(translator.translate_text("Please fill all required fields (including City).", st.session_state.language))
                    elif not re.match(phone_pattern, phone_clean):
                        st.error(translator.translate_text("Invalid phone number. Please enter a valid 10-digit Indian mobile number (starting with 6-9).", st.session_state.language))
                    elif len(password) < 6:
                        st.error(translator.translate_text("Password must be at least 6 characters long.", st.session_state.language))
                    else:
                        try:
                            user_id = db_manager.create_user(name, phone_clean, age, gender, password, selected_state, final_city)
                            if user_id:
                                st.session_state.user_id = user_id
                                st.session_state.user_name = name
                                st.success(translator.translate_text("Registration successful!", st.session_state.language))
                                st.rerun()
                            else:
                                st.error(translator.translate_text("Registration failed. Phone number may already exist.", st.session_state.language))
                        except Exception as e:
                            st.error(translator.translate_text(f"Registration failed: {str(e)}", st.session_state.language))

def show_dashboard():
    st.subheader(translator.translate_text("Health Dashboard", st.session_state.language))
    dashboard.render_dashboard(st.session_state.user_id, st.session_state.language)

def show_health_records():
    st.subheader(translator.translate_text("Health Records", st.session_state.language))
    
    # Display health records
    try:
        records = db_manager.get_health_records(st.session_state.user_id)
        
        if records:
            if pd is not None:
                df = pd.DataFrame(records)
                df.columns = ['ID', 'Date', 'Type', 'Description', 'Doctor', 'Hospital']
                try:
                    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
                except Exception:
                    pass
                st.dataframe(df, use_container_width=True)
            else:
                for r in records:
                    st.write(f"• {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]}")
        else:
            st.info("📋 " + translator.translate_text("No health records found. Add your first health record below to get started!", st.session_state.language))
    except Exception as e:
        st.error(translator.translate_text(f"Failed to load health records: {str(e)}", st.session_state.language))
    
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
                    try:
                        with st.spinner(translator.translate_text("Saving health record...", st.session_state.language)):
                            db_manager.add_health_record(
                                st.session_state.user_id, record_type, description,
                                doctor_name, hospital_name, record_date
                            )
                        st.success(translator.translate_text("Health record added successfully!", st.session_state.language))
                        st.rerun()
                    except Exception as e:
                        st.error(translator.translate_text(f"Failed to save health record: {str(e)}", st.session_state.language))

def show_clinical_notes():
    st.subheader("🩺 Clinical Notes (Beta)")
    if speech_notes_manager is None:
        st.error("❌ Speech-to-text module unavailable. Install faster-whisper to enable this feature.")
        st.info("💡 Run: pip install faster-whisper")
        return

    # Show status of speech module
    if speech_notes_manager.is_ready():
        st.success("✅ Speech-to-text module is ready!")
    else:
        if speech_notes_manager.last_error:
            st.error(f"❌ Speech module not ready: {speech_notes_manager.last_error}")
        else:
            st.warning("⚠️ Speech module is loading... Please wait a few seconds.")
        st.info("💡 Make sure faster-whisper is installed and FFmpeg is available.")

    summarizer_ready = summarizer_manager is not None and getattr(summarizer_manager, "client", None) is not None
    if not summarizer_ready:
        st.caption("ℹ️ LLM summarizer disabled. Set GEMINI_API_KEY in .env file to enable structured note generation.")
    if compute_wer is None:
        st.caption("ℹ️ Install jiwer to compute WER metrics.")

    st.caption("Record a doctor-patient conversation and store the raw transcript for future summarization.")

    language_options = {
        "Auto Detect": None,
        "English": "en",
        "Hindi": "hi",
        "Bengali": "bn",
        "Odia": "or",
        "Malayalam": "ml",
    }

    # Audio input outside form to avoid form reset issues
    audio_input = st.audio_input("🎙️ Record or upload audio", key="clinical_audio")
    
    # Show audio status
    audio_available = False
    if audio_input is not None:
        try:
            audio_bytes_test = audio_input.getvalue()
            if audio_bytes_test and len(audio_bytes_test) > 0:
                audio_available = True
                st.caption(f"✅ Audio loaded: {len(audio_bytes_test):,} bytes - Ready to transcribe!")
        except Exception:
            audio_available = False
    
    if not audio_available:
        st.info("💡 Record or upload audio above, then click 'Transcribe & Save' below")
    
    with st.form("clinical_note_form"):
        lang_choice = st.selectbox("Language override (optional)", list(language_options.keys()), index=0)
        
        # Store audio in session state to persist across form submissions
        if audio_input is not None:
            try:
                st.session_state['clinical_audio_bytes'] = audio_input.getvalue()
                st.session_state['clinical_audio_available'] = True
            except Exception:
                st.session_state['clinical_audio_available'] = False
        
        submitted = st.form_submit_button("Transcribe & Save", disabled=not st.session_state.get('clinical_audio_available', False))

        if submitted:
            # Get audio from session state (more reliable than from widget in form)
            audio_bytes = st.session_state.get('clinical_audio_bytes')
            
            if not audio_bytes or len(audio_bytes) == 0:
                # Try to get from widget as fallback
                if audio_input is not None:
                    try:
                        audio_bytes = audio_input.getvalue()
                    except Exception:
                        audio_bytes = None
                
                if not audio_bytes or len(audio_bytes) == 0:
                    st.error("No audio data received. Please record or upload audio again.")
                    st.info("💡 Tip: Make sure you've finished recording and the audio shows above before clicking 'Transcribe & Save'")
                else:
                    # Store in session state for next time
                    st.session_state['clinical_audio_bytes'] = audio_bytes
                    st.session_state['clinical_audio_available'] = True
            
            if audio_bytes and len(audio_bytes) > 0:
                    st.info(f"📊 Audio received: {len(audio_bytes):,} bytes")
                    try:
                        # Check if speech manager is ready
                        if not speech_notes_manager or not speech_notes_manager.is_ready():
                            st.error("Speech-to-text module is not ready. Please check if faster-whisper is installed and FFmpeg is available.")
                            if speech_notes_manager and speech_notes_manager.last_error:
                                st.warning(f"Error: {speech_notes_manager.last_error}")
                        else:
                            # Show progress with detailed steps
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            status_text.info("Step 1/3: Preparing audio file...")
                            progress_bar.progress(10)
                            
                            status_text.info("Step 2/3: Transcribing with Whisper (this may take 10-30 seconds)...")
                            progress_bar.progress(30)
                            
                            result = speech_notes_manager.transcribe_audio(
                                audio_bytes,
                                language_options[lang_choice],
                            )
                            
                            progress_bar.progress(90)
                            status_text.info("Step 3/3: Saving transcript to database...")
                                
                            if not result.text or result.text.strip() == "":
                                st.warning("⚠️ Transcription completed but no text was detected.")
                                st.info("💡 Tips: Ensure the audio is clear, contains speech, and is not too quiet.")
                                # Still save empty transcript for debugging
                                db_manager.save_clinical_transcript(
                                    st.session_state.user_id,
                                    "(empty transcript - no speech detected)",
                                    result.detected_language or language_options[lang_choice],
                                    speech_notes_manager.encode_audio(audio_bytes),
                                )
                                st.info("Empty transcript saved for review.")
                            else:
                                # Display preview of transcript
                                st.success("✅ Transcription successful!")
                                with st.expander("📝 Preview Transcript", expanded=True):
                                    st.write(result.text)
                                
                                db_manager.save_clinical_transcript(
                                    st.session_state.user_id,
                                    result.text,
                                    result.detected_language or language_options[lang_choice],
                                    speech_notes_manager.encode_audio(audio_bytes),
                                )
                                st.success(f"💾 Transcript saved! Detected language: {result.detected_language or 'Unknown'}")
                                st.rerun()
                    except Exception as exc:
                        error_msg = str(exc)
                        st.error(f"❌ Transcription failed: {error_msg}")
                        
                        # Provide helpful tips based on error
                        if "ffmpeg" in error_msg.lower():
                            st.info("💡 FFmpeg is required for audio conversion. Make sure FFmpeg is installed and in your PATH, or available in the project directory.")
                        elif "whisper model unavailable" in error_msg.lower() or "faster-whisper" in error_msg.lower():
                            st.info("💡 Make sure faster-whisper is installed: pip install faster-whisper")
                        elif "timeout" in error_msg.lower():
                            st.info("💡 Transcription timed out. Try with a shorter audio clip.")
                        
                        # Show detailed error in expander for debugging
                        with st.expander("🔍 Technical Error Details"):
                            st.exception(exc)

    st.markdown("### Previous Transcripts")
    transcripts = db_manager.get_clinical_transcripts(st.session_state.user_id)
    if not transcripts:
        st.info("No clinical transcripts yet. Record the first one above.")
    else:
        for note_id, transcript, source_lang, audio_b64, created_at in transcripts:
            label = f"Note #{note_id} – {created_at}"
            with st.expander(label, expanded=False):
                if source_lang:
                    st.caption(f"Source language: {source_lang}")
                st.write(transcript or "(empty)")
                if audio_b64:
                    try:
                        if speech_notes_manager is not None:
                            audio_bytes = speech_notes_manager.decode_audio(audio_b64)
                            st.audio(audio_bytes, format="audio/wav")
                        else:
                            st.caption("Audio playback unavailable (speech module not loaded).")
                    except Exception:
                        st.caption("Stored audio unavailable for playback.")

                summary = db_manager.get_clinical_summary(note_id)
                if summary:
                    (
                        chief_complaint,
                        symptoms,
                        medications,
                        findings,
                        plan,
                        follow_up,
                        additional_notes,
                        raw_response,
                        model_name,
                        summary_created,
                    ) = summary
                    st.markdown("**Structured Summary**")
                    st.write(f"- **Chief Complaint:** {chief_complaint}")
                    st.write(f"- **Symptoms:** {symptoms}")
                    st.write(f"- **Medications:** {medications}")
                    st.write(f"- **Findings:** {findings}")
                    st.write(f"- **Plan:** {plan}")
                    st.write(f"- **Follow-up:** {follow_up}")
                    st.write(f"- **Notes:** {additional_notes}")
                    st.caption(f"LLM: {model_name} | Generated: {summary_created}")
                elif summarizer_ready:
                    if st.button("Generate Structured Note", key=f"summarize_{note_id}"):
                        try:
                            with st.spinner("Summarizing via LLM..."):
                                structured = summarizer_manager.summarize(transcript)
                            db_manager.save_clinical_summary(note_id, structured.__dict__)
                            st.success("Structured note saved.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Summarization failed: {exc}")
                else:
                    st.info("Structured summary not available. Configure GEMINI_API_KEY in .env file to enable.")

                metrics = db_manager.get_clinical_metrics(note_id)
                if metrics:
                    reference_text, wer_value, rating, comments = metrics
                    st.markdown("**Evaluation Metrics**")
                    st.write(f"- **WER:** {wer_value:.3f}" if wer_value is not None else "- **WER:** N/A")
                    if rating:
                        st.write(f"- **Summary Rating:** {rating}/5")
                    if comments:
                        st.write(f"- **Comments:** {comments}")

                with st.form(f"metrics_form_{note_id}"):
                    st.markdown("**Evaluate Transcript Quality**")
                    reference_sample = st.text_area(
                        "Reference / ground truth text",
                        placeholder="Paste manual notes to compare...",
                        key=f"ref_{note_id}",
                    )
                    rating = st.slider(
                        "Summary accuracy rating (optional)",
                        min_value=1,
                        max_value=5,
                        value=4,
                        key=f"rating_{note_id}",
                    )
                    comments = st.text_input("Comments (optional)", key=f"comments_{note_id}")
                    submit_metrics = st.form_submit_button("Compute WER & Save")
                    if submit_metrics:
                        if not reference_sample.strip():
                            st.error("Provide a reference text to compute WER.")
                        elif compute_wer is None:
                            st.error("jiwer not installed; cannot compute WER.")
                        else:
                            try:
                                wer_value = compute_wer(reference_sample, transcript or "")
                                db_manager.save_clinical_metrics(
                                    note_id,
                                    reference_sample,
                                    float(wer_value),
                                    rating=rating,
                                    comments=comments or None,
                                )
                                st.success(f"Metrics saved (WER={wer_value:.3f}).")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Metric calculation failed: {exc}")

def show_upload_documents():
    st.subheader(translator.translate_text("Upload Medical Documents", st.session_state.language))
    
    uploaded_files = st.file_uploader(
        translator.translate_text("Choose medical documents", st.session_state.language),
        type=['pdf', 'jpg', 'jpeg', 'png'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        MAX_FILE_SIZE_MB = 10
        MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
        
        for uploaded_file in uploaded_files:
            # File size validation
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if uploaded_file.size > MAX_FILE_SIZE_BYTES:
                st.error(f"❌ {uploaded_file.name}: File too large ({file_size_mb:.2f} MB). Maximum size is {MAX_FILE_SIZE_MB} MB.")
                continue
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"📄 {uploaded_file.name} ({file_size_mb:.2f} MB)")
                
                # Show image preview for image files
                if uploaded_file.type.startswith('image'):
                    if Image is not None:
                        image = Image.open(uploaded_file)
                        st.image(image, width=300)
                    else:
                        st.image(uploaded_file, width=300)
            
            with col2:
                document_type = st.selectbox(
                    translator.translate_text("Document Type", st.session_state.language),
                    ["Prescription", "Lab Report", "X-Ray", "Scan", "Vaccination Card", "Other"],
                    key=f"type_{uploaded_file.name}"
                )
                
                if st.button(translator.translate_text("Save Document", st.session_state.language), key=f"save_{uploaded_file.name}"):
                    try:
                        with st.spinner(translator.translate_text("Saving document...", st.session_state.language)):
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
                        st.rerun()
                    except Exception as e:
                        st.error(translator.translate_text(f"Failed to save document: {str(e)}", st.session_state.language))
    
    # Display saved documents
    st.subheader(translator.translate_text("Saved Documents", st.session_state.language))
    try:
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
                            try:
                                image_bytes = base64.b64decode(doc[3])
                                if Image is not None:
                                    image = Image.open(io.BytesIO(image_bytes))
                                    st.image(image, caption=doc[1])
                                else:
                                    st.image(image_bytes, caption=doc[1])
                            except Exception as e:
                                st.error(f"Failed to display image: {str(e)}")
                with col3:
                    delete_key = f"delete_{doc[0]}"
                    confirm_key = f"confirm_delete_{doc[0]}"
                    
                    if st.session_state.get(confirm_key, False):
                        if st.button("⚠️ Confirm Delete", key=f"confirm_{doc[0]}", type="primary"):
                            try:
                                db_manager.delete_document(doc[0])
                                st.session_state[confirm_key] = False
                                st.success(translator.translate_text("Document deleted!", st.session_state.language))
                                st.rerun()
                            except Exception as e:
                                st.error(translator.translate_text(f"Failed to delete: {str(e)}", st.session_state.language))
                        if st.button("Cancel", key=f"cancel_{doc[0]}"):
                            st.session_state[confirm_key] = False
                            st.rerun()
                    else:
                        if st.button("Delete", key=delete_key):
                            st.session_state[confirm_key] = True
                            st.rerun()
        else:
            st.info(translator.translate_text("📭 No documents uploaded yet. Upload your first document above!", st.session_state.language))
    except Exception as e:
        st.error(translator.translate_text(f"Failed to load documents: {str(e)}", st.session_state.language))

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
    
    # Language selector for OCR (installed language packs must exist in Tesseract)
    col_lang1, col_lang2 = st.columns([1,1])
    with col_lang1:
        ocr_lang = st.selectbox(
            "OCR language",
            options=["eng", "eng+hin", "eng+tam", "eng+mar", "eng+ben"],
            index=0,
            help="Requires corresponding Tesseract language data installed."
        )

    uploaded_file = st.file_uploader(
        translator.translate_text("Upload prescription image", st.session_state.language),
        type=['jpg', 'jpeg', 'png'],
        help="Maximum file size: 10 MB"
    )
    
    if uploaded_file:
        # File size validation
        MAX_FILE_SIZE_MB = 10
        MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        if uploaded_file.size > MAX_FILE_SIZE_BYTES:
            st.error(f"❌ File too large ({file_size_mb:.2f} MB). Maximum size is {MAX_FILE_SIZE_MB} MB.")
        elif tesseract_ok:
            if Image is None:
                st.error("Pillow (PIL) not installed. Install with: pip install pillow")
                return
            image = Image.open(uploaded_file)
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.image(image, caption=translator.translate_text("Uploaded Prescription", st.session_state.language))
            
            with col2:
                if st.button(translator.translate_text("Analyze Prescription", st.session_state.language)):
                    try:
                        with st.spinner(translator.translate_text("Analyzing prescription...", st.session_state.language)):
                            # Perform OCR analysis
                            analysis_result = ocr_analyzer.analyze_prescription(image, st.session_state.language, tesseract_lang=ocr_lang)
                            
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
            try:
                with st.spinner(translator.translate_text("Loading hospital map...", st.session_state.language)):
                    # Generate and display map
                    hospital_map = sos_manager.get_nearest_hospitals_map(city)
                    if hospital_map:
                        try:
                            import streamlit.components.v1 as components
                            components.html(hospital_map._repr_html_(), height=400)
                        except Exception:
                            st.info(translator.translate_text("Unable to render map component. Update Streamlit to latest.", st.session_state.language))
                    
                    # Display hospital list
                    hospitals = sos_manager.get_hospital_list(city)
                    if hospitals:
                        st.subheader(translator.translate_text("Hospital List", st.session_state.language))
                        for hospital in hospitals:
                            st.write(f"🏥 {hospital}")
                    else:
                        st.info(translator.translate_text(f"No hospitals found for {city}. Try a different city.", st.session_state.language))
            except Exception as e:
                st.error(translator.translate_text(f"Failed to load hospital information: {str(e)}", st.session_state.language))
        
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
            # Show QR for this user
            with st.expander("My QR (Patient ID)"):
                try:
                    import qrcode
                    import io as _io
                    payload = st.session_state.get("qr_payload", f"AMITRA:{st.session_state.user_id}")
                    img = qrcode.make(payload)
                    buf = _io.BytesIO()
                    img.save(buf, format="PNG")
                    st.image(buf.getvalue(), caption=payload)
                    st.code(payload, language="text")
                except Exception as _e:
                    st.info("Install dependencies and reload to view QR.")
            
            # Display badges
            try:
                badges = db_manager.get_user_badges(st.session_state.user_id)
                if badges:
                    st.write(f"**{translator.translate_text('Badges Earned', st.session_state.language)}:**")
                    for badge in badges:
                        st.write(f"🏆 {badge}")
                else:
                    st.info("🏆 " + translator.translate_text("No badges earned yet. Keep adding health records to earn badges!", st.session_state.language))
            except Exception as e:
                st.caption(translator.translate_text(f"Unable to load badges: {str(e)}", st.session_state.language))
    
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
    except ImportError as e:
        st.error(translator.translate_text(f"Health chatbot module not available: {str(e)}", st.session_state.language))
        st.info(translator.translate_text("Please ensure health_chatbot.py exists and all dependencies are installed.", st.session_state.language))
    except Exception as e:
        st.error(translator.translate_text(f"Error loading health chatbot: {str(e)}", st.session_state.language))
        st.info(translator.translate_text("Please refresh the page or contact support if the problem persists.", st.session_state.language))

def show_qr_tools():
    """Generate and scan QR codes to fetch user records."""
    st.subheader("🔳 QR Tools")
    tabs = st.tabs(["Generate", "Scan"])
    with tabs[0]:
        st.caption("Patient QR encodes a simple payload: AMITRA:<user_id>")
        try:
            import qrcode, io as _io
            user_id_for_qr = st.session_state.get("user_id")
            if not user_id_for_qr:
                st.warning("Login required to generate QR.")
            else:
                payload = st.session_state.get("qr_payload", f"AMITRA:{user_id_for_qr}")
                img = qrcode.make(payload)
                buf = _io.BytesIO()
                img.save(buf, format="PNG")
                st.image(buf.getvalue(), caption=payload)
                st.download_button("Download QR", data=buf.getvalue(), file_name=f"patient_{user_id_for_qr}.png", mime="image/png")
        except Exception:
            st.info("Install qrcode to generate QR: pip install qrcode[pil]")

    with tabs[1]:
        st.caption("Use your webcam to scan a patient QR.")
        frame = st.camera_input("Scan QR")
        if frame is not None:
            try:
                import cv2, numpy as _np
            except Exception:
                st.info("Install OpenCV dependencies to scan: pip install opencv-python-headless numpy")
                return
            try:
                file_bytes = _np.asarray(bytearray(frame.getvalue()), dtype=_np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                detector = cv2.QRCodeDetector()
                data, pts, _ = detector.detectAndDecode(img)
                if data:
                    st.success(f"Decoded: {data}")
                    if data.startswith("AMITRA:"):
                        uid_part = data.split(":",1)[1]
                        if not uid_part.isdigit():
                            st.error("QR payload malformed")
                            return
                        uid = int(uid_part)
                        profile = db_manager.get_user_profile(uid)
                        if profile:
                            st.write(f"Name: {profile[1]} | Phone: {profile[2]} | Age: {profile[3]} | Gender: {profile[4]}")
                            # Show recent records
                            recs = db_manager.get_health_records(uid)
                            if recs:
                                import pandas as _pd
                                df = _pd.DataFrame(recs, columns=['ID','Date','Type','Description','Doctor','Hospital'])
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.info("No records for this user yet.")
                        else:
                            st.error("User not found.")
                    else:
                        st.warning("QR is not a valid Arogya-Mitra payload.")
                else:
                    st.error("Could not detect a QR code. Try again with better lighting.")
            except Exception as e:
                st.error(f"Scan error: {e}")

def show_worker_intake():
    """Worker Intake triage prototype: Has Prescription | No Prescription."""
    st.subheader(translator.translate_text("🛂 Worker Intake", st.session_state.language))
    if score_worker is None:
        st.info("Risk scoring module not available. Please ensure risk_scoring.py exists.")
        return

    tabs = st.tabs([
        translator.translate_text("Has Prescription", st.session_state.language),
        translator.translate_text("No Prescription", st.session_state.language),
    ])

    # Scenario A: Has Prescription
    with tabs[0]:
        uploaded = st.file_uploader(
            translator.translate_text("Upload prescription image", st.session_state.language),
            type=["jpg", "jpeg", "png"],
            key="intake_prescription_upload",
            help="Maximum file size: 10 MB"
        )
        vaccinated = st.checkbox(translator.translate_text("Vaccinated (recent/updated)", st.session_state.language), value=False)
        chronic_txt = st.text_input(translator.translate_text("Chronic conditions (comma-separated)", st.session_state.language), placeholder="diabetes, hypertension")

        if uploaded:
            # File size validation
            MAX_FILE_SIZE_MB = 10
            MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
            file_size_mb = uploaded.size / (1024 * 1024)
            
            if uploaded.size > MAX_FILE_SIZE_BYTES:
                st.error(f"❌ File too large ({file_size_mb:.2f} MB). Maximum size is {MAX_FILE_SIZE_MB} MB.")
            elif Image is None:
                st.error("Pillow (PIL) not installed. Install with: pip install pillow")
            else:
                try:
                    img = Image.open(uploaded)
                    st.image(img, caption="Prescription")
                    if st.button(translator.translate_text("Analyze & Score", st.session_state.language), key="intake_analyze_presc"):
                        with st.spinner(translator.translate_text("Analyzing prescription and calculating risk score...", st.session_state.language)):
                            try:
                                analysis_result = ocr_analyzer.analyze_prescription(img, st.session_state.language, tesseract_lang="eng")
                                extracted_text = (analysis_result or {}).get("extracted_text", "")
                                chronic_list = [c.strip() for c in (chronic_txt or "").split(",") if c.strip()]
                                outcome = score_worker(symptoms=[], chronic_conditions=chronic_list, vaccinated=vaccinated, extracted_text=extracted_text)

                                st.success(translator.translate_text("Scoring Complete", st.session_state.language))
                                _render_intake_report(outcome, source_text=extracted_text)
                            except Exception as e:
                                st.error(translator.translate_text(f"Intake analysis error: {str(e)}", st.session_state.language))
                                st.info(translator.translate_text("Please try again or contact support if the problem persists.", st.session_state.language))
                except Exception as e:
                    st.error(translator.translate_text(f"Failed to process image: {str(e)}", st.session_state.language))

    # Scenario B: No Prescription
    with tabs[1]:
        st.caption(translator.translate_text("Use QR or self-reported symptoms", st.session_state.language))
        # Optional QR flow: allow entering a user id decoded from QR
        col_qr1, col_qr2 = st.columns([1, 1])
        with col_qr1:
            uid_text = st.text_input("User ID from QR (optional)", value="")
        with col_qr2:
            vaccinated2 = st.checkbox(translator.translate_text("Vaccinated (recent/updated)", st.session_state.language), value=False, key="vaccinated2")

        # Self-reported symptoms
        st.write(translator.translate_text("Select symptoms:", st.session_state.language))
        symptom_options = ["fever", "cough", "fatigue", "rash", "breathlessness", "sore_throat", "body_ache", "headache"]
        symptom_cols = st.columns(4)
        selected_symptoms = []
        for idx, sname in enumerate(symptom_options):
            if symptom_cols[idx % 4].checkbox(sname.replace("_", " ").title(), key=f"symp_{sname}"):
                selected_symptoms.append(sname)

        chronic_txt2 = st.text_input(translator.translate_text("Chronic conditions (comma-separated)", st.session_state.language), placeholder="diabetes, hypertension", key="chronic2")

        # Aggregate records text if user id provided
        aggregated_text = ""
        if uid_text.strip().isdigit():
            try:
                uid_val = int(uid_text.strip())
                recs = db_manager.get_health_records(uid_val)
                if recs:
                    pieces = []
                    for r in recs:
                        pieces.append(str(r[3] or ""))  # description
                    aggregated_text = "\n".join(pieces)
            except Exception as e:
                st.info(f"Could not read records: {e}")

        if st.button(translator.translate_text("Score", st.session_state.language), key="intake_score_no_presc"):
            if not selected_symptoms and not chronic_txt2 and not aggregated_text:
                st.warning(translator.translate_text("Please provide at least one symptom, chronic condition, or user ID to calculate risk score.", st.session_state.language))
            else:
                try:
                    with st.spinner(translator.translate_text("Calculating risk score...", st.session_state.language)):
                        chronic_list2 = [c.strip() for c in (chronic_txt2 or "").split(",") if c.strip()]
                        outcome2 = score_worker(
                            symptoms=selected_symptoms,
                            chronic_conditions=chronic_list2,
                            vaccinated=vaccinated2,
                            extracted_text=aggregated_text,
                        )
                        st.success(translator.translate_text("Scoring Complete", st.session_state.language))
                        _render_intake_report(outcome2, source_text=aggregated_text)
                except Exception as e:
                    st.error(translator.translate_text(f"Failed to calculate risk score: {str(e)}", st.session_state.language))


def _render_intake_report(outcome: dict, source_text: str = ""):
    score = outcome.get("score", 0)
    bucket = outcome.get("bucket", "")
    hits = outcome.get("infectious_hits", [])
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Risk Score", f"{score}/100")
        st.metric("Classification", bucket)
    with col2:
        if hits:
            st.write("Potential infectious indicators:", ", ".join(hits))
        with st.expander("Source Text (for audit)"):
            st.text_area("", value=source_text or "", height=120, disabled=True)

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
