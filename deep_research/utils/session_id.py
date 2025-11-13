"""Session identifier utilities.

Provides a stable per-run session id accessible via a ContextVar so that
different parts of the system can emit artifacts under the same folder.
"""

from datetime import datetime, timezone
import uuid
from contextvars import ContextVar
from typing import Optional

_session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)


def _new_id() -> str:
    """Generate a new session id: ``YYYYmmddHHMMSS_<8 hex>``."""
    return (
        f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    )


def get_session_id() -> str:
    """Return the current session id, creating one if absent for this context."""
    sid = _session_id_var.get()
    if sid is None:
        _session_id_var.set(_new_id())
        sid = _session_id_var.get()
    return sid
