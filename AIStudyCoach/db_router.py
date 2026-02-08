import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def get_db_manager():
    """Return a DB manager instance based on env DB_BACKEND.

    DB_BACKEND: 'mysql' | 'sqlite' (default: sqlite for backward-compat)
    """
    backend = os.getenv("DB_BACKEND", "sqlite").lower()
    if backend == "mysql":
        from mysql_manager import MySQLDatabaseManager
        return MySQLDatabaseManager()
    else:
        from database import DatabaseManager
        return DatabaseManager()


