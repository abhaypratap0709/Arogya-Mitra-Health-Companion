import os
import mysql.connector
from mysql.connector import pooling
from datetime import datetime, date


class MySQLDatabaseManager:
    """MySQL-backed DB manager that mirrors the SQLite DatabaseManager API.

    Env vars used (with defaults for localhost dev):
      DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    """

    def __init__(self):
        self.host = os.getenv("DB_HOST", "127.0.0.1")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "arogya_mitra")

        # Ensure target database exists before creating pool
        self._ensure_database_exists()

        # Connection pool for efficiency in Streamlit reruns
        self.pool = pooling.MySQLConnectionPool(
            pool_name="arogya_pool",
            pool_size=5,
            pool_reset_session=True,
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            autocommit=True,
        )

        self.init_database()

    def _conn(self):
        return self.pool.get_connection()

    def _ensure_database_exists(self):
        """Create the database if it does not exist."""
        try:
            # Connect without specifying database
            bootstrap = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                autocommit=True,
            )
            cur = bootstrap.cursor()
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
            cur.close()
            bootstrap.close()
        except Exception:
            # If this fails, the subsequent pool creation will surface the error
            pass

    def init_database(self):
        """Create schema if not exists."""
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(32) UNIQUE NOT NULL,
                age INT,
                gender VARCHAR(16),
                state VARCHAR(128),
                city VARCHAR(128),
                password_hash VARCHAR(128) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                qr_payload VARCHAR(128) NULL,
                INDEX ix_users_phone (phone)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS health_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                record_type VARCHAR(64),
                description TEXT,
                doctor_name VARCHAR(255),
                hospital_name VARCHAR(255),
                record_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX ix_health_records_user_id (user_id),
                CONSTRAINT fk_hr_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                filename VARCHAR(255),
                document_type VARCHAR(64),
                file_data LONGBLOB,
                file_type VARCHAR(64),
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX ix_documents_user_id (user_id),
                CONSTRAINT fk_doc_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vital_signs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                measurement_type VARCHAR(64),
                value DOUBLE,
                unit VARCHAR(32),
                measurement_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX ix_vital_signs_user_id (user_id),
                CONSTRAINT fk_vs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prescription_analysis (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                filename VARCHAR(255),
                extracted_text MEDIUMTEXT,
                medications MEDIUMTEXT,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX ix_pa_user_id (user_id),
                CONSTRAINT fk_pa_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_badges (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                badge_name VARCHAR(128),
                earned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX ix_badges_user_id (user_id),
                CONSTRAINT fk_badge_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clinical_notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                transcript MEDIUMTEXT,
                source_language VARCHAR(16),
                audio_b64 LONGTEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX ix_clinical_notes_user_id (user_id),
                CONSTRAINT fk_clinical_notes_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clinical_note_summaries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                note_id INT NOT NULL,
                chief_complaint TEXT,
                symptoms TEXT,
                medications TEXT,
                findings TEXT,
                plan TEXT,
                follow_up TEXT,
                additional_notes TEXT,
                raw_response MEDIUMTEXT,
                model VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX ix_clinical_note_summaries_note_id (note_id),
                CONSTRAINT fk_clinical_note_summaries_note FOREIGN KEY (note_id) REFERENCES clinical_notes(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clinical_note_metrics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                note_id INT NOT NULL,
                reference_text MEDIUMTEXT,
                wer DOUBLE,
                summarization_rating INT,
                comments TEXT,
                INDEX ix_clinical_note_metrics_note_id (note_id),
                CONSTRAINT fk_clinical_note_metrics_note FOREIGN KEY (note_id) REFERENCES clinical_notes(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.close()
        conn.close()

    # ---- helpers ----
    @staticmethod
    def _norm_date(d):
        if d is None:
            return None
        if isinstance(d, datetime):
            return d
        if isinstance(d, date):
            return datetime(d.year, d.month, d.day)
        return datetime.fromisoformat(str(d)) if d else None

    # ---- API mirroring database.DatabaseManager ----
    def hash_password(self, password):
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, name, phone, age, gender, password, state=None, city=None):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (name, phone, age, gender, state, city, password_hash, qr_payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (name, phone, age, gender, state, city, self.hash_password(password), None),
        )
        user_id = cur.lastrowid
        cur.close()
        conn.close()
        return user_id

    def authenticate_user(self, phone, password):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name FROM users WHERE phone=%s AND password_hash=%s",
            (phone, self.hash_password(password)),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row

    def get_user_profile(self, user_id):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, phone, age, gender, state, city, created_at FROM users WHERE id=%s",
            (user_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row

    def add_health_record(self, user_id, record_type, description, doctor_name, hospital_name, record_date):
        if record_date is None:
            raise ValueError("record_date cannot be None")
        norm_date = self._norm_date(record_date)
        if norm_date is None:
            raise ValueError("Invalid date format for record_date")
        
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO health_records (user_id, record_type, description, doctor_name, hospital_name, record_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, record_type, description, doctor_name, hospital_name, norm_date.date()),
        )
        cur.close()
        conn.close()

    def get_health_records(self, user_id):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, record_date, record_type, description, doctor_name, hospital_name
            FROM health_records WHERE user_id=%s ORDER BY record_date DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def save_document(self, user_id, filename, document_type, file_data, file_type):
        # Expect base64 string; store as bytes
        import base64
        blob = base64.b64decode(file_data) if isinstance(file_data, str) else file_data
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO documents (user_id, filename, document_type, file_data, file_type)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, filename, document_type, blob, file_type),
        )
        cur.close()
        conn.close()

    def get_user_documents(self, user_id):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, filename, document_type, file_data, upload_date, file_type
            FROM documents WHERE user_id=%s ORDER BY upload_date DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        # Convert BLOB to base64 string to keep front-end unchanged
        import base64
        out = []
        for (doc_id, name, dtype, blob, udate, ftype) in rows:
            b64 = base64.b64encode(blob).decode() if blob is not None else None
            out.append((doc_id, name, dtype, b64, udate, ftype))
        return out

    def delete_document(self, document_id):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM documents WHERE id=%s", (document_id,))
        cur.close()
        conn.close()

    def add_vital_sign(self, user_id, measurement_type, value, unit, measurement_date=None):
        conn = self._conn()
        cur = conn.cursor()
        md = self._norm_date(measurement_date) or datetime.utcnow()
        cur.execute(
            """
            INSERT INTO vital_signs (user_id, measurement_type, value, unit, measurement_date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, measurement_type, value, unit, md),
        )
        cur.close()
        conn.close()

    def get_vital_signs(self, user_id, measurement_type=None, days=30):
        conn = self._conn()
        cur = conn.cursor()
        if measurement_type:
            cur.execute(
                """
                SELECT measurement_type, value, unit, measurement_date
                FROM vital_signs
                WHERE user_id=%s AND measurement_type=%s AND measurement_date >= (NOW() - INTERVAL %s DAY)
                ORDER BY measurement_date DESC
                """,
                (user_id, measurement_type, int(days)),
            )
        else:
            cur.execute(
                """
                SELECT measurement_type, value, unit, measurement_date
                FROM vital_signs
                WHERE user_id=%s AND measurement_date >= (NOW() - INTERVAL %s DAY)
                ORDER BY measurement_date DESC
                """,
                (user_id, int(days)),
            )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def save_prescription_analysis(self, user_id, filename, extracted_text, medications):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO prescription_analysis (user_id, filename, extracted_text, medications)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, filename, extracted_text, medications),
        )
        cur.close()
        conn.close()

    def add_badge(self, user_id, badge_name):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM user_badges WHERE user_id=%s AND badge_name=%s",
            (user_id, badge_name),
        )
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO user_badges (user_id, badge_name) VALUES (%s, %s)",
                (user_id, badge_name),
            )
        cur.close()
        conn.close()

    def get_user_badges(self, user_id):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT badge_name FROM user_badges WHERE user_id=%s ORDER BY earned_date DESC",
            (user_id,),
        )
        rows = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows

    # Admin helpers
    def get_all_users_basic(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, phone FROM users ORDER BY created_at DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def update_user(self, user_id, name=None, phone=None, age=None, gender=None, state=None, city=None, password=None):
        fields = []
        values = []
        if name is not None:
            fields.append("name=%s"); values.append(name)
        if phone is not None:
            fields.append("phone=%s"); values.append(phone)
        if age is not None:
            fields.append("age=%s"); values.append(age)
        if gender is not None:
            fields.append("gender=%s"); values.append(gender)
        if state is not None:
            fields.append("state=%s"); values.append(state)
        if city is not None:
            fields.append("city=%s"); values.append(city)
        if password is not None:
            fields.append("password_hash=%s"); values.append(self.hash_password(password))
        if not fields:
            return False
        values.append(user_id)
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=%s", tuple(values))
        cur.close()
        conn.close()
        return True

    def delete_user(self, user_id):
        conn = self._conn()
        cur = conn.cursor()
        try:
            # Start transaction
            cur.execute("START TRANSACTION")
            
            # Delete dependents first (in correct order due to foreign keys)
            # Delete clinical note metrics first
            cur.execute("""
                DELETE FROM clinical_note_metrics 
                WHERE note_id IN (SELECT id FROM clinical_notes WHERE user_id=%s)
            """, (user_id,))
            # Delete clinical note summaries
            cur.execute("""
                DELETE FROM clinical_note_summaries 
                WHERE note_id IN (SELECT id FROM clinical_notes WHERE user_id=%s)
            """, (user_id,))
            # Delete clinical notes
            cur.execute("DELETE FROM clinical_notes WHERE user_id=%s", (user_id,))
            # Delete other dependents (CASCADE should handle these, but explicit is safer)
            cur.execute("DELETE FROM health_records WHERE user_id=%s", (user_id,))
            cur.execute("DELETE FROM documents WHERE user_id=%s", (user_id,))
            cur.execute("DELETE FROM vital_signs WHERE user_id=%s", (user_id,))
            cur.execute("DELETE FROM prescription_analysis WHERE user_id=%s", (user_id,))
            cur.execute("DELETE FROM user_badges WHERE user_id=%s", (user_id,))
            # Finally delete user
            cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def get_health_records_for_user(self, user_id):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, record_date, record_type, description, doctor_name, hospital_name
            FROM health_records WHERE user_id=%s ORDER BY record_date DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def update_health_record(self, record_id, record_type=None, description=None, doctor_name=None, hospital_name=None, record_date=None):
        fields, values = [], []
        if record_type is not None:
            fields.append("record_type=%s"); values.append(record_type)
        if description is not None:
            fields.append("description=%s"); values.append(description)
        if doctor_name is not None:
            fields.append("doctor_name=%s"); values.append(doctor_name)
        if hospital_name is not None:
            fields.append("hospital_name=%s"); values.append(hospital_name)
        if record_date is not None:
            fields.append("record_date=%s"); values.append(self._norm_date(record_date).date())
        if not fields:
            return False
        values.append(record_id)
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(f"UPDATE health_records SET {', '.join(fields)} WHERE id=%s", tuple(values))
        cur.close()
        conn.close()
        return True

    def delete_health_record(self, record_id):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM health_records WHERE id=%s", (record_id,))
        cur.close()
        conn.close()
        return True

    # Clinical notes
    def save_clinical_transcript(self, user_id, transcript, source_language=None, audio_b64=None):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO clinical_notes (user_id, transcript, source_language, audio_b64)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, transcript, source_language, audio_b64),
        )
        note_id = cur.lastrowid
        cur.close()
        conn.close()
        return note_id

    def get_clinical_transcripts(self, user_id):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, transcript, source_language, audio_b64, created_at
            FROM clinical_notes
            WHERE user_id=%s
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def save_clinical_summary(self, note_id, summary_dict):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO clinical_note_summaries (
                note_id, chief_complaint, symptoms, medications,
                findings, plan, follow_up, additional_notes,
                raw_response, model
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                note_id,
                summary_dict.get("chief_complaint"),
                summary_dict.get("symptoms"),
                summary_dict.get("medications"),
                summary_dict.get("findings"),
                summary_dict.get("plan"),
                summary_dict.get("follow_up"),
                summary_dict.get("additional_notes"),
                summary_dict.get("raw_response"),
                summary_dict.get("model"),
            ),
        )
        conn.commit()
        cur.close()
        conn.close()

    def get_clinical_summary(self, note_id):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT chief_complaint, symptoms, medications, findings,
                   plan, follow_up, additional_notes, raw_response, model, created_at
            FROM clinical_note_summaries
            WHERE note_id=%s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (note_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row

    def save_clinical_metrics(self, note_id, reference_text, wer_value, rating=None, comments=None):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO clinical_note_metrics (
                note_id, reference_text, wer, summarization_rating, comments
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (note_id, reference_text, wer_value, rating, comments),
        )
        conn.commit()
        cur.close()
        conn.close()

    def get_clinical_metrics(self, note_id):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT reference_text, wer, summarization_rating, comments
            FROM clinical_note_metrics
            WHERE note_id=%s
            ORDER BY id DESC
            LIMIT 1
            """,
            (note_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row


