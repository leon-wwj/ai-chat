import uuid


def new_request_id() -> str:
    """Short per-request id, so log lines of concurrent requests stay tellable apart."""
    return uuid.uuid4().hex[:8]
