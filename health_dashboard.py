import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from translator import TranslationManager

class HealthDashboard:
    def __init__(self, db_manager):
        self.db = db_manager
        self.translator = TranslationManager()
    
    def render_dashboard(self, user_id, language='en'):
        """Render the main health dashboard"""
        
        # Health Score Section
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            health_score = self.calculate_health_score(user_id)
            st.metric(
                self.translator.translate_text("Health Score", language),
                f"{health_score}/100",
                delta=self.get_health_score_trend(user_id)
            )
        
        with col2:
            record_count = len(self.db.get_health_records(user_id))
            st.metric(
                self.translator.translate_text("Health Records", language),
                record_count
            )
        
        with col3:
            badge_count = len(self.db.get_user_badges(user_id))
            st.metric(
                self.translator.translate_text("Badges Earned", language),
                badge_count
            )
        
        # Quick Actions with persistent toggles
        st.subheader(self.translator.translate_text("Quick Actions", language))
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📊 " + self.translator.translate_text("Log Vitals", language)):
                st.session_state.show_vitals_form = True

        with col2:
            if st.button("💊 " + self.translator.translate_text("Medication Reminder", language)):
                st.session_state.show_medication_reminders = True

        with col3:
            if st.button("📋 " + self.translator.translate_text("Add Record", language)):
                st.session_state.show_record_form = True

        with col4:
            if st.button("🏆 " + self.translator.translate_text("View Achievements", language)):
                st.session_state.show_achievements = True
        
        # Conditional sections triggered by Quick Actions
        if st.session_state.get('show_vitals_form', False):
            self.show_vitals_input(user_id, language)

        if st.session_state.get('show_medication_reminders', False):
            self.show_medication_reminders(user_id, language)

        if st.session_state.get('show_achievements', False):
            self.show_achievements(user_id, language)

        # Vital Signs Charts
        self.render_vital_signs_charts(user_id, language)
        
        # Inline Add Record form when toggled
        if st.session_state.get('show_record_form', False):
            with st.expander(self.translator.translate_text("Add New Health Record", language), expanded=True):
                with st.form("inline_health_record_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        record_type = st.selectbox(
                            self.translator.translate_text("Record Type", language),
                            ["Consultation", "Lab Report", "Prescription", "Vaccination", "Surgery", "Other"]
                        )
                        doctor_name = st.text_input(self.translator.translate_text("Doctor Name", language))
                        hospital_name = st.text_input(self.translator.translate_text("Hospital/Clinic Name", language))
                    with col2:
                        description = st.text_area(self.translator.translate_text("Description", language))
                        record_date = st.date_input(self.translator.translate_text("Date", language), value=datetime.now().date())
                    submitted = st.form_submit_button(self.translator.translate_text("Add Record", language))
                    if submitted and description:
                        self.db.add_health_record(user_id, record_type, description, doctor_name, hospital_name, record_date)
                        st.session_state.show_record_form = False
                        st.success(self.translator.translate_text("Health record added successfully!", language))
                        st.rerun()

        # Recent Activity
        self.render_recent_activity(user_id, language)
        
        # Health Tips
        self.render_health_tips(language)
        
        # Check and award badges
        self.check_and_award_badges(user_id)
    
    def show_vitals_input(self, user_id, language):
        """Show vital signs input form"""
        st.subheader(self.translator.translate_text("Log Vital Signs", language))
        
        with st.form("vitals_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                vital_type = st.selectbox(
                    self.translator.translate_text("Measurement Type", language),
                    ["Blood Pressure", "Heart Rate", "Temperature", "Weight", "Blood Sugar", "Oxygen Saturation"]
                )
                
                value = st.number_input(
                    self.translator.translate_text("Value", language),
                    min_value=0.0,
                    step=0.1
                )
            
            with col2:
                unit_options = {
                    "Blood Pressure": "mmHg",
                    "Heart Rate": "bpm",
                    "Temperature": "°F",
                    "Weight": "kg",
                    "Blood Sugar": "mg/dL",
                    "Oxygen Saturation": "%"
                }
                
                unit = st.text_input(
                    self.translator.translate_text("Unit", language),
                    value=unit_options.get(vital_type, "")
                )
                
                measurement_date = st.date_input(
                    self.translator.translate_text("Date", language),
                    value=datetime.now().date()
                )
            
            submitted = st.form_submit_button(self.translator.translate_text("Log Measurement", language))
            
            if submitted and value > 0:
                self.db.add_vital_sign(user_id, vital_type, value, unit, measurement_date)
                st.success(self.translator.translate_text("Vital sign logged successfully!", language))
                st.rerun()
    
    def render_vital_signs_charts(self, user_id, language):
        """Render vital signs charts"""
        st.subheader(self.translator.translate_text("Vital Signs Trends", language))
        
        # Get vital signs data
        vitals = self.db.get_vital_signs(user_id)
        
        if vitals:
            df = pd.DataFrame(vitals)
            df.columns = ['Type', 'Value', 'Unit', 'Date']
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Create separate charts for different vital types
            vital_types = df['Type'].unique()
            
            if len(vital_types) > 0:
                tabs = st.tabs([f"{vtype}" for vtype in vital_types])
                
                for i, vital_type in enumerate(vital_types):
                    with tabs[i]:
                        type_data = df[df['Type'] == vital_type]
                        
                        if len(type_data) > 1:
                            fig = px.line(
                                type_data, 
                                x='Date', 
                                y='Value',
                                title=f"{vital_type} Trend",
                                markers=True
                            )
                            fig.update_layout(
                                xaxis_title=self.translator.translate_text("Date", language),
                                yaxis_title=f"{vital_type} ({type_data.iloc[0]['Unit']})"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info(self.translator.translate_text("Need more data points to show trend", language))
        else:
            st.info(self.translator.translate_text("No vital signs data available. Start logging your measurements!", language))
    
    def render_recent_activity(self, user_id, language):
        """Render recent activity section"""
        st.subheader(self.translator.translate_text("Recent Activity", language))
        
        # Get recent health records
        records = self.db.get_health_records(user_id)
        recent_records = records[:5]  # Last 5 records
        
        if recent_records:
            for record in recent_records:
                with st.expander(f"📋 {record[2]} - {record[1]}"):
                    st.write(f"**{self.translator.translate_text('Description', language)}:** {record[3]}")
                    if record[4]:
                        st.write(f"**{self.translator.translate_text('Doctor', language)}:** {record[4]}")
                    if record[5]:
                        st.write(f"**{self.translator.translate_text('Hospital', language)}:** {record[5]}")
        else:
            st.info(self.translator.translate_text("No recent activity. Start by adding health records!", language))
    
    def render_health_tips(self, language):
        """Render health tips section"""
        st.subheader(self.translator.translate_text("Daily Health Tips", language))
        
        health_tips = [
            "Drink at least 8 glasses of water daily",
            "Take a 30-minute walk every day",
            "Eat plenty of fruits and vegetables",
            "Get 7-8 hours of sleep each night",
            "Practice deep breathing exercises",
            "Limit processed foods and sugar intake",
            "Wash your hands frequently",
            "Take regular breaks from screen time"
        ]
        
        # Translate tips
        translated_tips = []
        for tip in health_tips:
            translated_tip = self.translator.translate_text(tip, language)
            translated_tips.append(translated_tip)
        
        # Show random tip of the day
        import random
        tip_of_day = random.choice(translated_tips)
        
        st.info(f"💡 **{self.translator.translate_text('Tip of the Day', language)}:** {tip_of_day}")
    
    def show_medication_reminders(self, user_id, language):
        """Show medication reminders (placeholder)"""
        st.subheader(self.translator.translate_text("Medication Reminders", language))
        st.info(self.translator.translate_text("Set up medication reminders to never miss a dose!", language))
        
        # Placeholder for medication reminder functionality
        with st.form("reminder_form"):
            medication_name = st.text_input(self.translator.translate_text("Medication Name", language))
            reminder_time = st.time_input(self.translator.translate_text("Reminder Time", language))
            frequency = st.selectbox(
                self.translator.translate_text("Frequency", language),
                ["Once daily", "Twice daily", "Three times daily", "As needed"]
            )
            
            if st.form_submit_button(self.translator.translate_text("Set Reminder", language)):
                st.success(self.translator.translate_text("Reminder set successfully!", language))
    
    def show_achievements(self, user_id, language):
        """Show user achievements and badges"""
        st.subheader(self.translator.translate_text("Achievements & Badges", language))
        
        badges = self.db.get_user_badges(user_id)
        
        if badges:
            # Display badges in a grid
            cols = st.columns(3)
            for i, badge in enumerate(badges):
                with cols[i % 3]:
                    badge_emoji = self.get_badge_emoji(badge)
                    st.write(f"{badge_emoji} **{badge}**")
        else:
            st.info(self.translator.translate_text("No badges earned yet. Keep using the app to unlock achievements!", language))
        
        # Show available badges to earn
        st.subheader(self.translator.translate_text("Badges to Earn", language))
        
        available_badges = [
            "First Health Record",
            "Vital Signs Tracker",
            "One Week Streak",
            "Document Uploader",
            "Health Champion"
        ]
        
        earned_badge_names = [badge for badge in badges]
        
        for badge in available_badges:
            if badge not in earned_badge_names:
                badge_emoji = self.get_badge_emoji(badge)
                st.write(f"{badge_emoji} {badge} - {self.get_badge_description(badge, language)}")
    
    def calculate_health_score(self, user_id):
        """Calculate user's health score"""
        score = 50  # Base score
        
        # Add points for health records
        records = self.db.get_health_records(user_id)
        score += min(len(records) * 5, 20)  # Max 20 points
        
        # Add points for vital signs tracking
        vitals = self.db.get_vital_signs(user_id)
        score += min(len(vitals) * 2, 15)  # Max 15 points
        
        # Add points for document uploads
        documents = self.db.get_user_documents(user_id)
        score += min(len(documents) * 3, 15)  # Max 15 points
        
        return min(score, 100)
    
    def get_health_score_trend(self, user_id):
        """Get health score trend (placeholder)"""
        # In a real implementation, this would compare with previous period
        return "+5"
    
    def check_and_award_badges(self, user_id):
        """Check and award badges based on user activity"""
        records = self.db.get_health_records(user_id)
        vitals = self.db.get_vital_signs(user_id)
        documents = self.db.get_user_documents(user_id)
        
        # Award badges based on criteria
        if len(records) >= 1:
            self.db.add_badge(user_id, "First Health Record")
        
        if len(vitals) >= 5:
            self.db.add_badge(user_id, "Vital Signs Tracker")
        
        if len(documents) >= 1:
            self.db.add_badge(user_id, "Document Uploader")
        
        if len(records) >= 10:
            self.db.add_badge(user_id, "Health Champion")
    
    def get_badge_emoji(self, badge_name):
        """Get emoji for badge"""
        badge_emojis = {
            "First Health Record": "🏆",
            "Vital Signs Tracker": "📊",
            "One Week Streak": "🔥",
            "Document Uploader": "📤",
            "Health Champion": "👑"
        }
        return badge_emojis.get(badge_name, "🏅")
    
    def get_badge_description(self, badge_name, language):
        """Get badge description"""
        descriptions = {
            "First Health Record": "Add your first health record",
            "Vital Signs Tracker": "Log 5 vital sign measurements",
            "One Week Streak": "Use the app for 7 consecutive days",
            "Document Uploader": "Upload your first medical document",
            "Health Champion": "Add 10 health records"
        }
        
        description = descriptions.get(badge_name, "Complete the challenge to earn this badge")
        return self.translator.translate_text(description, language)
