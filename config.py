import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TONCENTER_API_KEY = os.environ.get("TONCENTER_API_KEY", "").strip()
TONCENTER_BASE = "https://toncenter.com/api/v2"
POLL_INTERVAL_SEC = int(os.environ.get("POLL_INTERVAL_SEC", "45"))

# Optional: https://www.trongrid.io/ (public works without key, but key increases limits)
TRONGRID_API_KEY = os.environ.get("TRONGRID_API_KEY", "").strip()
