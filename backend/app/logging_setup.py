import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("ai_chat")

# httpx logs every single request at INFO; our own lines already cover that,
# so keep it out of the way unless it warns about something real.
logging.getLogger("httpx").setLevel(logging.WARNING)
