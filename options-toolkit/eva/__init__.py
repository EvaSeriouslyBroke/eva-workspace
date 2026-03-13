"""Eva — unified options analysis and paper trading toolkit."""

import os
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
MAJOR_DIV = "=" * 40
MINOR_DIV = "\u2500" * 40  # ─

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.join(SCRIPT_DIR, "data")
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".openclaw", "tradier.json")
DISCORD_CHANNEL = "1479499260188950671"
