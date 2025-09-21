import sqlite3
import hashlib
from datetime import datetime, date

class DatabaseManager:
    def __init__(self, db_path="arogya_mitra.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                age INTEGER,
                gender TEXT,
                state TEXT,
                city TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if state and city columns exist, if not add them
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'state' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN state TEXT")
        
        if 'city' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN city TEXT")
        
        conn.commit()
        
        # Health records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                record_type TEXT,
                description TEXT,
                doctor_name TEXT,
                hospital_name TEXT,
                record_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT,
                document_type TEXT,
                file_data TEXT,
                file_type TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Vital signs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vital_signs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                measurement_type TEXT,
                value REAL,
                unit TEXT,
                measurement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Prescription analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prescription_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT,
                extracted_text TEXT,
                medications TEXT,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Badges/achievements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                badge_name TEXT,
                earned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, name, phone, age, gender, password, state=None, city=None):
        """Create a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (name, phone, age, gender, state, city, password_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, phone, age, gender, state, city, password_hash))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            return None
    
    def authenticate_user(self, phone, password):
        """Authenticate user with phone and password"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        
        cursor.execute('''
            SELECT id, name FROM users 
            WHERE phone = ? AND password_hash = ?
        ''', (phone, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        return user
    
    def get_user_profile(self, user_id):
        """Get user profile data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, phone, age, gender, state, city, created_at
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        return user
    
    def add_health_record(self, user_id, record_type, description, doctor_name, hospital_name, record_date):
        """Add a new health record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO health_records (user_id, record_type, description, doctor_name, hospital_name, record_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, record_type, description, doctor_name, hospital_name, record_date))
        
        conn.commit()
        conn.close()
    
    def get_health_records(self, user_id):
        """Get all health records for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, record_date, record_type, description, doctor_name, hospital_name
            FROM health_records 
            WHERE user_id = ?
            ORDER BY record_date DESC
        ''', (user_id,))
        
        records = cursor.fetchall()
        conn.close()
        return records
    
    def save_document(self, user_id, filename, document_type, file_data, file_type):
        """Save uploaded document"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO documents (user_id, filename, document_type, file_data, file_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, filename, document_type, file_data, file_type))
        
        conn.commit()
        conn.close()
    
    def get_user_documents(self, user_id):
        """Get all documents for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, document_type, file_data, upload_date, file_type
            FROM documents 
            WHERE user_id = ?
            ORDER BY upload_date DESC
        ''', (user_id,))
        
        documents = cursor.fetchall()
        conn.close()
        return documents
    
    def delete_document(self, document_id):
        """Delete a document"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM documents WHERE id = ?', (document_id,))
        
        conn.commit()
        conn.close()
    
    def add_vital_sign(self, user_id, measurement_type, value, unit, measurement_date=None):
        """Add vital sign measurement"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if measurement_date is not None:
            # Normalize date/datetime to string acceptable by SQLite
            if isinstance(measurement_date, datetime):
                md = measurement_date.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(measurement_date, date):
                md = measurement_date.strftime('%Y-%m-%d')
            else:
                md = str(measurement_date)

            cursor.execute('''
                INSERT INTO vital_signs (user_id, measurement_type, value, unit, measurement_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, measurement_type, value, unit, md))
        else:
            cursor.execute('''
                INSERT INTO vital_signs (user_id, measurement_type, value, unit)
                VALUES (?, ?, ?, ?)
            ''', (user_id, measurement_type, value, unit))

        conn.commit()
        conn.close()
    
    def get_vital_signs(self, user_id, measurement_type=None, days=30):
        """Get vital signs for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if measurement_type:
            cursor.execute('''
                SELECT measurement_type, value, unit, measurement_date
                FROM vital_signs 
                WHERE user_id = ? AND measurement_type = ?
                AND measurement_date >= date('now', '-{} days')
                ORDER BY measurement_date DESC
            '''.format(days), (user_id, measurement_type))
        else:
            cursor.execute('''
                SELECT measurement_type, value, unit, measurement_date
                FROM vital_signs 
                WHERE user_id = ?
                AND measurement_date >= date('now', '-{} days')
                ORDER BY measurement_date DESC
            '''.format(days), (user_id,))
        
        vitals = cursor.fetchall()
        conn.close()
        return vitals
    
    def save_prescription_analysis(self, user_id, filename, extracted_text, medications):
        """Save prescription analysis results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO prescription_analysis (user_id, filename, extracted_text, medications)
            VALUES (?, ?, ?, ?)
        ''', (user_id, filename, extracted_text, medications))
        
        conn.commit()
        conn.close()
    
    def add_badge(self, user_id, badge_name):
        """Add a badge to user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if badge already exists
        cursor.execute('''
            SELECT id FROM user_badges 
            WHERE user_id = ? AND badge_name = ?
        ''', (user_id, badge_name))
        
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO user_badges (user_id, badge_name)
                VALUES (?, ?)
            ''', (user_id, badge_name))
            
            conn.commit()
        
        conn.close()
    
    def get_user_badges(self, user_id):
        """Get all badges for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT badge_name FROM user_badges 
            WHERE user_id = ?
            ORDER BY earned_date DESC
        ''', (user_id,))
        
        badges = [row[0] for row in cursor.fetchall()]
        conn.close()
        return badges
