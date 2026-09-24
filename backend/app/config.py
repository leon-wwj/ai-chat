DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"
TIMEOUT_SECONDS = 60

# Retry policy for upstream calls: only failures that can plausibly succeed on a
# later attempt (transport errors, rate limits, server errors). Client errors such
# as 400/401/404 are returned immediately - retrying them would just waste time.
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 0.5
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
