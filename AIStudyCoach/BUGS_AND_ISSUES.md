# 🐛 Critical Bugs and Issues Found

## 🔴 CRITICAL BUGS (Fix Immediately)

### Bug 1: SQL Injection Vulnerability
**File**: `database.py`  
**Lines**: 333, 341  
**Severity**: CRITICAL - Security Risk

**Issue**: Using `.format()` for SQL queries instead of parameterized queries

```python
# BUGGY CODE (Lines 333, 341):
cursor.execute('''
    SELECT measurement_type, value, unit, measurement_date
    FROM vital_signs 
    WHERE user_id = ? AND measurement_type = ?
    AND measurement_date >= date('now', '-{} days')
    ORDER BY measurement_date DESC
'''.format(days), (user_id, measurement_type))
```

**Fix**: Use parameterized queries properly:
```python
cursor.execute('''
    SELECT measurement_type, value, unit, measurement_date
    FROM vital_signs 
    WHERE user_id = ? AND measurement_type = ?
    AND measurement_date >= date('now', '-' || ? || ' days')
    ORDER BY measurement_date DESC
''', (user_id, measurement_type, days))
```

---

### Bug 2: Null Pointer Exception
**File**: `mysql_manager.py`  
**Line**: 251  
**Severity**: CRITICAL - Will crash if record_date is None

**Issue**: `self._norm_date(record_date).date()` will fail if `record_date` is None

```python
# BUGGY CODE:
(user_id, record_type, description, doctor_name, hospital_name, self._norm_date(record_date).date()),
```

**Fix**: Add null check:
```python
norm_date = self._norm_date(record_date)
if norm_date is None:
    raise ValueError("record_date cannot be None")
(user_id, record_type, description, doctor_name, hospital_name, norm_date.date()),
```

---

### Bug 3: Missing Data Deletion in delete_user()
**File**: `database.py`  
**Lines**: 447-460  
**Severity**: HIGH - Data inconsistency

**Issue**: `delete_user()` doesn't delete `clinical_notes` and related tables

**Current code**:
```python
def delete_user(self, user_id):
    # Delete dependents first
    cursor.execute('DELETE FROM health_records WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM documents WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM vital_signs WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM prescription_analysis WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM user_badges WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    # MISSING: clinical_notes, clinical_note_summaries, clinical_note_metrics
```

**Fix**: Add missing deletions:
```python
def delete_user(self, user_id):
    # Delete dependents first (in correct order due to foreign keys)
    cursor.execute('DELETE FROM clinical_note_metrics WHERE note_id IN (SELECT id FROM clinical_notes WHERE user_id = ?)', (user_id,))
    cursor.execute('DELETE FROM clinical_note_summaries WHERE note_id IN (SELECT id FROM clinical_notes WHERE user_id = ?)', (user_id,))
    cursor.execute('DELETE FROM clinical_notes WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM health_records WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM documents WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM vital_signs WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM prescription_analysis WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM user_badges WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
```

**Same issue in**: `mysql_manager.py` line 434-439

---

### Bug 4: Missing Transaction Handling
**File**: `database.py`, `mysql_manager.py`  
**Function**: `delete_user()`  
**Severity**: HIGH - Data corruption risk

**Issue**: Multiple DELETE operations without transaction - if one fails, data becomes inconsistent

**Fix**: Wrap in transaction:
```python
def delete_user(self, user_id):
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    try:
        # Start transaction
        cursor.execute('BEGIN TRANSACTION')
        
        # All delete operations...
        cursor.execute('DELETE FROM clinical_note_metrics WHERE note_id IN (SELECT id FROM clinical_notes WHERE user_id = ?)', (user_id,))
        # ... other deletes ...
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()
```

---

## 🟡 HIGH PRIORITY ISSUES

### Issue 5: Missing Error Handling in Database Operations
**File**: Multiple files  
**Severity**: HIGH

**Issues**:
- Many database operations don't handle exceptions properly
- Connections might not be closed on errors
- No logging of database errors

**Example**: `database.py` line 198-212 - `authenticate_user()` has no try-except

**Fix**: Add proper error handling:
```python
def authenticate_user(self, phone, password):
    conn = None
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        password_hash = self.hash_password(password)
        cursor.execute('''
            SELECT id, name FROM users 
            WHERE phone = ? AND password_hash = ?
        ''', (phone, password_hash))
        user = cursor.fetchone()
        return user
    except sqlite3.Error as e:
        # Log error
        print(f"Database error in authenticate_user: {e}")
        return None
    finally:
        if conn:
            conn.close()
```

---

### Issue 6: Missing Input Validation
**File**: `app.py`  
**Severity**: MEDIUM-HIGH

**Issues**:
- Phone number validation exists but could be bypassed
- File size validation happens after upload (should be before)
- No validation for SQL injection in search fields
- No rate limiting on login attempts

**Fix**: Add comprehensive validation:
```python
# In show_registration_login():
phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
if not re.match(r'^[6-9]\d{9}$', phone_clean):
    st.error("Invalid phone number")
    return  # Don't proceed
```

---

### Issue 7: Resource Leaks
**File**: Multiple database files  
**Severity**: MEDIUM

**Issues**:
- Some database connections might not be closed if exceptions occur
- No use of context managers

**Fix**: Use context managers or ensure finally blocks:
```python
# Better approach:
def get_user_profile(self, user_id):
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ... FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()
```

---

### Issue 8: Missing Null Checks
**File**: Multiple files  
**Severity**: MEDIUM

**Issues**:
- `app.py` line 251: `self._norm_date(record_date).date()` - no null check
- Many places assume database returns non-null values
- No validation for empty strings vs None

**Fix**: Add null checks:
```python
if record_date is None:
    raise ValueError("record_date is required")
norm_date = self._norm_date(record_date)
if norm_date is None:
    raise ValueError("Invalid date format")
```

---

## 🟢 MEDIUM PRIORITY ISSUES

### Issue 9: Inconsistent Error Messages
**File**: `app.py`  
**Severity**: LOW-MEDIUM

**Issue**: Error messages are sometimes in English, sometimes translated. Should be consistent.

**Fix**: Always use translator for user-facing messages.

---

### Issue 10: Missing Index on Foreign Keys
**File**: `database.py` (init_database)  
**Severity**: LOW-MEDIUM

**Issue**: Some foreign keys don't have indexes, which can slow down queries.

**Fix**: Add indexes for all foreign keys:
```python
cursor.execute("CREATE INDEX IF NOT EXISTS ix_clinical_notes_user_id ON clinical_notes(user_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS ix_clinical_note_summaries_note_id ON clinical_note_summaries(note_id);")
```

---

### Issue 11: Hardcoded Admin Credentials
**File**: `admin_portal.py`  
**Lines**: 17-20  
**Severity**: MEDIUM (Security)

**Issue**: Admin credentials are hardcoded in source code.

**Fix**: Move to database or environment variables (already mentioned in improvements doc).

---

### Issue 12: Missing Clinical Notes Cleanup
**File**: `database.py`, `mysql_manager.py`  
**Severity**: MEDIUM

**Issue**: When deleting a user, clinical notes are not deleted (cascade should handle this, but explicit is better).

**Fix**: Already covered in Bug 3.

---

### Issue 13: Potential Division by Zero
**File**: `admin_portal.py`  
**Line**: 290  
**Severity**: LOW

**Issue**: `avg_records = round(total_reports / total_users, 2)` can divide by zero.

**Fix**:
```python
avg_records = round(total_reports / total_users, 2) if total_users > 0 else 0
```

---

### Issue 14: Missing Validation for File Types
**File**: `app.py`  
**Severity**: LOW-MEDIUM

**Issue**: File type validation happens but could be more strict.

**Fix**: Add MIME type validation in addition to extension check.

---

## 📋 Summary

### Critical (Fix Now):
1. ✅ SQL Injection in `database.py` lines 333, 341
2. ✅ Null pointer in `mysql_manager.py` line 251
3. ✅ Missing clinical_notes deletion in `delete_user()`
4. ✅ Missing transaction handling in `delete_user()`

### High Priority:
5. ✅ Missing error handling in database operations
6. ✅ Missing input validation
7. ✅ Resource leaks
8. ✅ Missing null checks

### Medium Priority:
9. ✅ Inconsistent error messages
10. ✅ Missing indexes
11. ✅ Hardcoded credentials
12. ✅ Division by zero risk
13. ✅ File type validation

---

## 🔧 Quick Fix Priority

1. **Fix SQL Injection** (Bug 1) - 5 minutes
2. **Fix Null Pointer** (Bug 2) - 2 minutes
3. **Fix delete_user** (Bug 3) - 5 minutes
4. **Add Transaction** (Bug 4) - 5 minutes
5. **Add Error Handling** (Issue 5) - 30 minutes

**Total estimated time**: ~1 hour for critical fixes

