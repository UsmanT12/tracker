"""Legacy configuration retained for reference.

The replacement application uses typed settings in ``backend/app/core/config.py``.
"""

import os

CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH", "")
SCHEDULE_URL = os.getenv(
    "WNBA_SCHEDULE_URL",
    "https://www.wnba.com/schedule?season=2024&month=all",
)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "wnba_stats")
DB_USER = os.getenv("DB_USER", "wnba_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_PORT = os.getenv("DB_PORT", "5432")
