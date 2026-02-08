import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
from db_router import get_db_manager
from translator import TranslationManager
from indian_states_cities import get_states, get_cities_for_state

class AdminPortal:
    def __init__(self):
        self.db = get_db_manager()
        self.translator = TranslationManager()
        
        # Hardcoded admin credentials
        self.admin_credentials = {
            "admin": "admin123",
            "superadmin": "super123"
        }
    
    def authenticate_admin(self, username, password):
        """Authenticate admin user"""
        return self.admin_credentials.get(username) == password
    
    def get_total_users(self):
        """Get total number of users (works for SQLite or MySQL backend)."""
        if hasattr(self.db, "db_path"):
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        else:
            conn = self.db._conn()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
            cur.close(); conn.close()
            return count
    
    def get_total_reports(self):
        """Get total number of health records (SQLite or MySQL)."""
        if hasattr(self.db, "db_path"):
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM health_records")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        else:
            conn = self.db._conn(); cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM health_records")
            count = cur.fetchone()[0]
            cur.close(); conn.close()
            return count
    
    def get_city_wise_users(self):
        """Get city-wise user distribution (SQLite or MySQL)."""
        if hasattr(self.db, "db_path"):
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(city, 'Not Specified') as city, 
                    COALESCE(state, 'Not Specified') as state, 
                    COUNT(*) as user_count 
                FROM users 
                GROUP BY city, state 
                ORDER BY user_count DESC
            """)
            data = cursor.fetchall()
            conn.close()
        else:
            conn = self.db._conn(); cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COALESCE(city, 'Not Specified') as city, 
                    COALESCE(state, 'Not Specified') as state, 
                    COUNT(*) as user_count 
                FROM users 
                GROUP BY city, state 
                ORDER BY user_count DESC
            """)
            data = cur.fetchall()
            cur.close(); conn.close()
        df = pd.DataFrame(data, columns=['City', 'State', 'User Count'])
        return df
    
    def get_all_users(self):
        """Get all users with basic details (SQLite or MySQL)."""
        if hasattr(self.db, "db_path"):
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id, name, phone, age, gender, 
                    COALESCE(state, 'Not Specified') as state, 
                    COALESCE(city, 'Not Specified') as city, 
                    created_at
                FROM users 
                ORDER BY created_at DESC
            """)
            data = cursor.fetchall()
            conn.close()
        else:
            conn = self.db._conn(); cur = conn.cursor()
            cur.execute("""
                SELECT 
                    id, name, phone, age, gender, 
                    COALESCE(state, 'Not Specified') as state, 
                    COALESCE(city, 'Not Specified') as city, 
                    created_at
                FROM users 
                ORDER BY created_at DESC
            """)
            data = cur.fetchall()
            cur.close(); conn.close()
        df = pd.DataFrame(data, columns=[
            'ID', 'Name', 'Phone', 'Age', 'Gender', 'State', 'City', 'Joined Date'
        ])
        return df
    
    def get_disease_analysis(self):
        """Analyze diseases/health records by state (SQLite or MySQL)."""
        if hasattr(self.db, "db_path"):
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(u.state, 'Not Specified') as state, 
                    hr.record_type, 
                    COUNT(*) as count
                FROM health_records hr
                JOIN users u ON hr.user_id = u.id
                GROUP BY u.state, hr.record_type
                ORDER BY u.state, count DESC
            """)
            data = cursor.fetchall()
            conn.close()
        else:
            conn = self.db._conn(); cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COALESCE(u.state, 'Not Specified') as state, 
                    hr.record_type, 
                    COUNT(*) as count
                FROM health_records hr
                JOIN users u ON hr.user_id = u.id
                GROUP BY u.state, hr.record_type
                ORDER BY u.state, count DESC
            """)
            data = cur.fetchall()
            cur.close(); conn.close()
        df = pd.DataFrame(data, columns=['State', 'Record Type', 'Count'])
        return df

    def get_clinical_note_count(self):
        query = "SELECT COUNT(*) FROM clinical_notes"
        if hasattr(self.db, "db_path"):
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            count = cursor.fetchone()[0]
            conn.close()
        else:
            conn = self.db._conn(); cur = conn.cursor()
            cur.execute(query)
            count = cur.fetchone()[0]
            cur.close(); conn.close()
        return count

    def get_average_wer(self):
        query = "SELECT AVG(wer) FROM clinical_note_metrics WHERE wer IS NOT NULL"
        if hasattr(self.db, "db_path"):
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute(query)
                value = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                value = None
            conn.close()
        else:
            conn = self.db._conn(); cur = conn.cursor()
            cur.execute(query)
            value = cur.fetchone()[0]
            cur.close(); conn.close()
        return value
    
    def get_common_diseases_by_state(self):
        """Get most common diseases/conditions by state (SQLite or MySQL)."""
        if hasattr(self.db, "db_path"):
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(u.state, 'Not Specified') as state, 
                    hr.record_type, 
                    COUNT(*) as count
                FROM health_records hr
                JOIN users u ON hr.user_id = u.id
                WHERE hr.record_type IN ('Consultation', 'Lab Report', 'Prescription', 'Surgery')
                GROUP BY u.state, hr.record_type
                ORDER BY u.state, count DESC
            """)
            data = cursor.fetchall()
            conn.close()
        else:
            conn = self.db._conn(); cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COALESCE(u.state, 'Not Specified') as state, 
                    hr.record_type, 
                    COUNT(*) as count
                FROM health_records hr
                JOIN users u ON hr.user_id = u.id
                WHERE hr.record_type IN ('Consultation', 'Lab Report', 'Prescription', 'Surgery')
                GROUP BY u.state, hr.record_type
                ORDER BY u.state, count DESC
            """)
            data = cur.fetchall()
            cur.close(); conn.close()

        state_diseases = {}
        for state, record_type, count in data:
            if state not in state_diseases:
                state_diseases[state] = []
            state_diseases[state].append((record_type, count))
        result = []
        for state, diseases in state_diseases.items():
            if diseases:
                top_disease = max(diseases, key=lambda x: x[1])
                result.append({
                    'State': state,
                    'Most Common Condition': top_disease[0],
                    'Count': top_disease[1]
                })
        return pd.DataFrame(result)
    
    def render_admin_login(self):
        """Render admin login page"""
        st.title("🔐 Admin Portal Login")
        
        # Warning message
        st.warning("⚠️ **Admin Access Only** - This portal is separate from user accounts and requires special admin credentials.")
        
        with st.form("admin_login"):
            username = st.text_input("Admin Username")
            password = st.text_input("Admin Password", type="password")
            submitted = st.form_submit_button("Login as Admin")
            
            if submitted:
                if self.authenticate_admin(username, password):
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_username = username
                    st.success("Admin login successful!")
                    st.rerun()
                else:
                    st.error("Invalid admin credentials!")
        
        # Show available credentials for demo
        with st.expander("Demo Credentials"):
            st.code("""
            Username: admin
            Password: admin123
            
            Username: superadmin  
            Password: super123
            """)
    
    def render_admin_dashboard(self):
        """Render main admin dashboard"""
        st.title("📊 Admin Dashboard")
        
        # Top metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_users = self.get_total_users()
            st.metric("Total Users", total_users)
        
        with col2:
            total_reports = self.get_total_reports()
            st.metric("Total Health Records", total_reports)
        
        with col3:
            # Calculate average records per user
            avg_records = round(total_reports / total_users, 2) if total_users > 0 else 0
            st.metric("Avg Records/User", avg_records)
        
        with col4:
            # Get users registered in last 30 days
            if hasattr(self.db, "db_path"):
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE created_at >= date('now', '-30 days')
                """)
                recent_users = cursor.fetchone()[0]
                conn.close()
            else:
                conn = self.db._conn(); cur = conn.cursor()
                cur.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE created_at >= (NOW() - INTERVAL 30 DAY)
                """)
                recent_users = cur.fetchone()[0]
                cur.close(); conn.close()
            st.metric("New Users (30 days)", recent_users)

        # AI notes metrics
        note_col1, note_col2 = st.columns(2)
        with note_col1:
            st.metric("Clinical Notes Captured", self.get_clinical_note_count())
        with note_col2:
            avg_wer = self.get_average_wer()
            st.metric("Average WER", f"{avg_wer:.3f}" if avg_wer is not None else "N/A")
        
        # City-wise distribution
        st.subheader("🏙️ City-wise User Distribution")
        
        city_data = self.get_city_wise_users()
        
        if not city_data.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Bar chart
                fig = px.bar(
                    city_data.head(20), 
                    x='User Count', 
                    y='City',
                    orientation='h',
                    title="Top 20 Cities by User Count",
                    color='User Count',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Table
                st.subheader("City Distribution Table")
                st.dataframe(
                    city_data.head(10),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("No city data available yet.")
        
        # Disease analysis by state
        st.subheader("🏥 Health Conditions by State")
        
        disease_data = self.get_common_diseases_by_state()
        
        if not disease_data.empty:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Bar chart for diseases by state
                fig = px.bar(
                    disease_data,
                    x='State',
                    y='Count',
                    color='Most Common Condition',
                    title="Most Common Health Conditions by State"
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Disease distribution table
                st.subheader("Disease Analysis Table")
                st.dataframe(
                    disease_data,
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("No health record data available for analysis.")
    
    def render_user_management(self):
        """Render user management page"""
        st.title("👥 User Management")
        
        # Search and filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("Search by name or phone", placeholder="Enter search term")
        
        with col2:
            state_filter = st.selectbox("Filter by State", ["All"] + get_states())
        
        with col3:
            gender_filter = st.selectbox("Filter by Gender", ["All", "Male", "Female", "Other"])
        
        # Get all users
        users_df = self.get_all_users()
        
        # Apply filters
        if search_term:
            users_df = users_df[
                users_df['Name'].str.contains(search_term, case=False, na=False) |
                users_df['Phone'].str.contains(search_term, case=False, na=False)
            ]
        
        if state_filter != "All":
            users_df = users_df[users_df['State'] == state_filter]
        
        if gender_filter != "All":
            users_df = users_df[users_df['Gender'] == gender_filter]
        
        # Display user count
        st.write(f"**Total Users Found:** {len(users_df)}")
        
        # Pagination
        if len(users_df) > 0:
            page_size = 20
            total_pages = (len(users_df) - 1) // page_size + 1
            
            if 'user_page' not in st.session_state:
                st.session_state.user_page = 1
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("Previous") and st.session_state.user_page > 1:
                    st.session_state.user_page -= 1
                    st.rerun()
            
            with col2:
                st.write(f"Page {st.session_state.user_page} of {total_pages}")
            
            with col3:
                if st.button("Next") and st.session_state.user_page < total_pages:
                    st.session_state.user_page += 1
                    st.rerun()
            
            # Display users for current page
            start_idx = (st.session_state.user_page - 1) * page_size
            end_idx = start_idx + page_size
            page_users = users_df.iloc[start_idx:end_idx]
            
            st.dataframe(
                page_users,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No users found matching the criteria.")

        st.markdown("---")
        st.subheader("✏️ User CRUD")

        tab_create, tab_update = st.tabs(["Create User", "Update/Delete User"])

        with tab_create:
            with st.form("admin_create_user"):
                col1, col2 = st.columns(2)
                with col1:
                    c_name = st.text_input("Full Name *")
                    c_phone = st.text_input("Phone *")
                    c_age = st.number_input("Age *", min_value=1, max_value=120, value=30)
                    c_gender = st.selectbox("Gender *", ["Male", "Female", "Other"])
                with col2:
                    c_state = st.text_input("State")
                    c_city = st.text_input("City")
                    c_password = st.text_input("Password *", type="password")
                c_submit = st.form_submit_button("Create User")
                if c_submit:
                    if all([c_name.strip(), c_phone.strip(), c_password.strip()]):
                        user_id = self.db.create_user(c_name, c_phone, int(c_age), c_gender, c_password, c_state or None, c_city or None)
                        if user_id:
                            st.success(f"User created with ID {user_id}")
                        else:
                            st.error("Create failed. Phone may already exist.")
                    else:
                        st.error("Please fill required fields (Name, Phone, Password)")

        with tab_update:
            # Selection list for users
            users_basic = self.db.get_all_users_basic()
            user_options = {f"{u[1]} ({u[2]}) [ID:{u[0]}]": u[0] for u in users_basic}
            selected_label = st.selectbox("Select User", list(user_options.keys())) if user_options else None
            if selected_label:
                user_id = user_options[selected_label]
                profile = self.db.get_user_profile(user_id)
                if profile:
                    with st.form("admin_update_user"):
                        col1, col2 = st.columns(2)
                        with col1:
                            u_name = st.text_input("Full Name", value=profile[1] or "")
                            u_phone = st.text_input("Phone", value=profile[2] or "")
                            u_age = st.number_input("Age", min_value=1, max_value=120, value=int(profile[3]) if profile[3] else 30)
                            u_gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=( ["Male","Female","Other"].index(profile[4]) if profile[4] in ["Male","Female","Other"] else 0))
                        with col2:
                            u_state = st.text_input("State", value=profile[5] or "")
                            u_city = st.text_input("City", value=profile[6] or "")
                            u_password = st.text_input("Reset Password (optional)", type="password")
                        colu1, colu2 = st.columns(2)
                        with colu1:
                            do_update = st.form_submit_button("Save Changes")
                        with colu2:
                            do_delete = st.form_submit_button("Delete User", type="secondary")

                    if do_update:
                        self.db.update_user(
                            user_id,
                            name=u_name.strip(),
                            phone=u_phone.strip(),
                            age=int(u_age),
                            gender=u_gender,
                            state=u_state.strip() or None,
                            city=u_city.strip() or None,
                            password=u_password.strip() or None
                        )
                        st.success("User updated")
                        st.rerun()

                    if do_delete:
                        self.db.delete_user(user_id)
                        st.success("User deleted")
                        st.rerun()

                # Health Records management for this user
                st.markdown("---")
                st.subheader("🗂️ Health Records for Selected User")
                records = self.db.get_health_records_for_user(user_id)
                if records:
                    rec_df = pd.DataFrame(records, columns=['ID','Date','Type','Description','Doctor','Hospital'])
                    st.dataframe(rec_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No records yet for this user.")

                # Add new record
                with st.expander("Add New Record"):
                    with st.form("admin_add_record"):
                        r_type = st.selectbox("Record Type", ["Consultation","Lab Report","Prescription","Vaccination","Surgery","Other"])
                        r_desc = st.text_area("Description *")
                        r_doc = st.text_input("Doctor Name *")
                        r_hosp = st.text_input("Hospital/Clinic Name *")
                        r_date = st.date_input("Date *")
                        r_add = st.form_submit_button("Add Record")
                        if r_add:
                            if all([r_desc.strip(), r_doc.strip(), r_hosp.strip(), r_date]):
                                self.db.add_health_record(user_id, r_type, r_desc, r_doc, r_hosp, r_date)
                                st.success("Record added")
                                st.rerun()
                            else:
                                st.error("Fill all required fields")

                # Update/Delete existing record
                if records:
                    with st.expander("Edit/Delete Record"):
                        record_map = {f"{r[0]} - {r[2]} - {r[1]}": r for r in records}
                        selected_rec_label = st.selectbox("Select Record", list(record_map.keys()))
                        rid, rdate, rtype, rdesc, rdoc, rhosp = record_map[selected_rec_label]
                        with st.form("admin_edit_record"):
                            e_type = st.selectbox("Record Type", ["Consultation","Lab Report","Prescription","Vaccination","Surgery","Other"], index=["Consultation","Lab Report","Prescription","Vaccination","Surgery","Other"].index(rtype) if rtype in ["Consultation","Lab Report","Prescription","Vaccination","Surgery","Other"] else 0)
                            e_desc = st.text_area("Description *", value=rdesc or "")
                            e_doc = st.text_input("Doctor Name *", value=rdoc or "")
                            e_hosp = st.text_input("Hospital/Clinic Name *", value=rhosp or "")
                            e_date = st.date_input("Date *", value=pd.to_datetime(rdate).date() if rdate else None)
                            colr1, colr2 = st.columns(2)
                            with colr1:
                                rec_update = st.form_submit_button("Save Changes")
                            with colr2:
                                rec_delete = st.form_submit_button("Delete Record", type="secondary")

                        if rec_update:
                            if all([e_desc.strip(), e_doc.strip(), e_hosp.strip(), e_date]):
                                self.db.update_health_record(rid, record_type=e_type, description=e_desc, doctor_name=e_doc, hospital_name=e_hosp, record_date=e_date)
                                st.success("Record updated")
                                st.rerun()
                            else:
                                st.error("Fill all required fields")
                        if rec_delete:
                            self.db.delete_health_record(rid)
                            st.success("Record deleted")
                            st.rerun()
    
    def render_analytics(self):
        """Render analytics page"""
        st.title("📈 Analytics & Reports")
        
        # User registration trends
        st.subheader("📊 User Registration Trends")
        
        if hasattr(self.db, "db_path"):
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM users
                WHERE created_at >= date('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            trend_data = cursor.fetchall()
            conn.close()
        else:
            conn = self.db._conn(); cur = conn.cursor()
            cur.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM users
                WHERE created_at >= (NOW() - INTERVAL 30 DAY)
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            trend_data = cur.fetchall()
            cur.close(); conn.close()
        
        if trend_data:
            trend_df = pd.DataFrame(trend_data, columns=['Date', 'New Users'])
            trend_df['Date'] = pd.to_datetime(trend_df['Date'])
            
            fig = px.line(trend_df, x='Date', y='New Users', title="Daily User Registrations (Last 30 Days)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No registration data available for the last 30 days.")
        
        # Gender distribution
        st.subheader("👥 Gender Distribution")
        
        if hasattr(self.db, "db_path"):
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT gender, COUNT(*) as count FROM users GROUP BY gender")
            gender_data = cursor.fetchall()
            conn.close()
        else:
            conn = self.db._conn(); cur = conn.cursor()
            cur.execute("SELECT gender, COUNT(*) as count FROM users GROUP BY gender")
            gender_data = cur.fetchall()
            cur.close(); conn.close()
        
        if gender_data:
            gender_df = pd.DataFrame(gender_data, columns=['Gender', 'Count'])
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                fig = px.pie(gender_df, values='Count', names='Gender', title="Gender Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.dataframe(gender_df, use_container_width=True, hide_index=True)
        
        # Age distribution
        st.subheader("🎂 Age Distribution")
        
        if hasattr(self.db, "db_path"):
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN age < 18 THEN 'Under 18'
                        WHEN age BETWEEN 18 AND 30 THEN '18-30'
                        WHEN age BETWEEN 31 AND 50 THEN '31-50'
                        WHEN age BETWEEN 51 AND 70 THEN '51-70'
                        ELSE 'Over 70'
                    END as age_group,
                    COUNT(*) as count
                FROM users
                WHERE age IS NOT NULL
                GROUP BY age_group
                ORDER BY 
                    CASE 
                        WHEN age_group = 'Under 18' THEN 1
                        WHEN age_group = '18-30' THEN 2
                        WHEN age_group = '31-50' THEN 3
                        WHEN age_group = '51-70' THEN 4
                        ELSE 5
                    END
            """)
            age_data = cursor.fetchall()
            conn.close()
        else:
            conn = self.db._conn(); cur = conn.cursor()
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN age < 18 THEN 'Under 18'
                        WHEN age BETWEEN 18 AND 30 THEN '18-30'
                        WHEN age BETWEEN 31 AND 50 THEN '31-50'
                        WHEN age BETWEEN 51 AND 70 THEN '51-70'
                        ELSE 'Over 70'
                    END as age_group,
                    COUNT(*) as count
                FROM users
                WHERE age IS NOT NULL
                GROUP BY age_group
                ORDER BY 
                    FIELD(age_group,'Under 18','18-30','31-50','51-70','Over 70')
            """)
            age_data = cur.fetchall()
            cur.close(); conn.close()
        
        if age_data:
            age_df = pd.DataFrame(age_data, columns=['Age Group', 'Count'])
            fig = px.bar(age_df, x='Age Group', y='Count', title="Age Group Distribution")
            st.plotly_chart(fig, use_container_width=True)
    
    def render_admin_portal(self):
        """Main admin portal renderer"""
        # Clear any user session when accessing admin portal
        if 'user_id' in st.session_state:
            del st.session_state['user_id']
        if 'user_name' in st.session_state:
            del st.session_state['user_name']
        
        if not st.session_state.get('admin_logged_in', False):
            self.render_admin_login()
        else:
            # Admin navigation
            st.sidebar.title(f"Welcome, {st.session_state.admin_username}")
            
            if st.sidebar.button("Logout"):
                # Clear all admin session data
                if 'admin_logged_in' in st.session_state:
                    del st.session_state['admin_logged_in']
                if 'admin_username' in st.session_state:
                    del st.session_state['admin_username']
                st.rerun()
            
            # Admin pages
            admin_pages = {
                "Dashboard": "📊 Dashboard",
                "User Management": "👥 User Management", 
                "Analytics": "📈 Analytics"
            }
            
            selected_page = st.sidebar.radio("Navigation", list(admin_pages.keys()))
            
            if selected_page == "Dashboard":
                self.render_admin_dashboard()
            elif selected_page == "User Management":
                self.render_user_management()
            elif selected_page == "Analytics":
                self.render_analytics()
