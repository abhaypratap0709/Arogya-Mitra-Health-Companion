import streamlit as st
from datetime import datetime

def init_session_state():
    """Initialize session state variables"""
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    
    if 'emergency_activated' not in st.session_state:
        st.session_state.emergency_activated = False
    
    if 'show_record_form' not in st.session_state:
        st.session_state.show_record_form = False

def get_language_options():
    """Get available language options"""
    return {
        "English": "en",
        "हिंदी (Hindi)": "hi", 
        "বাংলা (Bengali)": "bn",
        "ଓଡ଼ିଆ (Odia)": "or",
        "മലയാളം (Malayalam)": "ml"
    }

def format_date(date_obj):
    """Format date for display"""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime("%Y-%m-%d")

def validate_phone_number(phone):
    """Validate Indian phone number"""
    import re
    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, phone))

def get_file_size_mb(file_obj):
    """Get file size in MB"""
    if hasattr(file_obj, 'size'):
        return file_obj.size / (1024 * 1024)
    return 0

def is_image_file(filename):
    """Check if file is an image"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    return any(filename.lower().endswith(ext) for ext in image_extensions)

def is_pdf_file(filename):
    """Check if file is a PDF"""
    return filename.lower().endswith('.pdf')

def generate_user_id():
    """Generate a unique user ID"""
    import uuid
    return str(uuid.uuid4())[:8]

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re
    # Remove special characters except dots and underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return sanitized

def get_current_timestamp():
    """Get current timestamp as string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_medical_date(date_string):
    """Parse various date formats commonly found in medical documents"""
    import re
    from datetime import datetime
    
    # Common date patterns in medical documents
    patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
        r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})',  # DD MMM YYYY
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_string, re.IGNORECASE)
        if match:
            try:
                if 'Jan' in pattern:  # Month name pattern
                    day, month_name, year = match.groups()
                    month_map = {
                        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                        'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                        'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                    }
                    month = month_map.get(month_name[:3].title(), 1)
                    return datetime(int(year), month, int(day)).date()
                else:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # YYYY first
                        year, month, day = groups
                    else:  # DD first
                        day, month, year = groups
                    return datetime(int(year), int(month), int(day)).date()
            except ValueError:
                continue
    
    return None

def extract_phone_numbers(text):
    """Extract phone numbers from text"""
    import re
    # Indian phone number patterns
    patterns = [
        r'\+91[- ]?[6-9]\d{9}',  # +91 followed by 10 digits
        r'[6-9]\d{9}',  # 10 digit mobile number
        r'0\d{2,3}[- ]?\d{7,8}'  # Landline numbers
    ]
    
    phone_numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        phone_numbers.extend(matches)
    
    return list(set(phone_numbers))  # Remove duplicates

def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI"""
    if weight_kg <= 0 or height_cm <= 0:
        return None
    
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 1)

def get_bmi_category(bmi):
    """Get BMI category"""
    if bmi is None:
        return "Unknown"
    elif bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def is_emergency_keyword(text):
    """Check if text contains emergency keywords"""
    emergency_keywords = [
        'emergency', 'urgent', 'critical', 'severe', 'acute',
        'pain', 'bleeding', 'unconscious', 'breathing', 'chest pain',
        'heart attack', 'stroke', 'accident', 'injury', 'fever'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in emergency_keywords)

def get_app_version():
    """Get application version"""
    return "1.0.0"

def log_user_activity(user_id, activity_type, details=None):
    """Log user activity (placeholder for analytics)"""
    activity_log = {
        'user_id': user_id,
        'activity': activity_type,
        'timestamp': get_current_timestamp(),
        'details': details
    }
    # In a real app, this would be saved to a logging system
    print(f"Activity logged: {activity_log}")
