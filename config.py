import os
from pathlib import Path

APP_NAME = "OpenFlashcards"
APP_VERSION = "2.0.0"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("OPENFLASHCARDS_DATA_DIR", Path.home() / ".openflashcards"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "openflashcards.db"

# Spaced Repetition Constants
DEFAULT_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3
MAX_BOX = 5
CRITICAL_RETENTION_THRESHOLD = 0.50  # Cards below 50% retention flagged as heavily overdue
