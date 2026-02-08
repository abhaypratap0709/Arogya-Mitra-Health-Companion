# Quick Admin Access
# Run this file to access admin portal directly

import streamlit as st
from admin_portal import AdminPortal

st.set_page_config(
    page_title="Admin Portal - Arogya Mitra",
    page_icon="⚙️",
    layout="wide"
)

admin_portal = AdminPortal()
admin_portal.render_admin_portal()
