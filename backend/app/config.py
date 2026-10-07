import os
from pathlib import Path

from dotenv import load_dotenv

# 读取 backend/.env（该文件不进 git）
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "")

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"
TIMEOUT_SECONDS = 60

# Streaming cannot use one total timeout: a long answer legitimately runs for
# minutes, and a hard cap would kill it mid-sentence. So it is split in two:
#   idle   - max gap between two data chunks (mapped to httpx's read timeout)
#   budget - hard cap on the whole stream, checked while data keeps arriving
STREAM_IDLE_TIMEOUT_SECONDS = 30.0
STREAM_TOTAL_BUDGET_SECONDS = 300.0

# Retry policy for upstream calls: only failures that can plausibly succeed on a
# later attempt (transport errors, rate limits, server errors). Client errors such
# as 400/401/404 are returned immediately - retrying them would just waste time.
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 0.5
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
