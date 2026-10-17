"""
Database configuration template.

Copy this file to config/db_config.py (which is gitignored) and either edit the
defaults below or set the SHELFSENSE_DB_* environment variables / a .env file.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_CONFIG = {
    "host": os.getenv("SHELFSENSE_DB_HOST", "localhost"),
    "port": int(os.getenv("SHELFSENSE_DB_PORT", "5432")),
    "user": os.getenv("SHELFSENSE_DB_USER", "postgres"),
    "password": os.getenv("SHELFSENSE_DB_PASSWORD", "postgres"),
    "dbname": os.getenv("SHELFSENSE_DB_NAME", "shelfsense"),
}


CONNECTION_STRING = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)
