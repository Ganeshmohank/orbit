import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

SESSIONS_DIR = Path("sessions")
USERS_DIR = Path("users")


def ensure_dirs():
    """Create necessary directories if they don't exist."""
    SESSIONS_DIR.mkdir(exist_ok=True)
    USERS_DIR.mkdir(exist_ok=True)


def get_user_file(uid: str) -> Path:
    """Get the user data file path."""
    ensure_dirs()
    return USERS_DIR / f"{uid}.json"


def get_session_file(uid: str) -> Path:
    """Get the session file path."""
    ensure_dirs()
    return SESSIONS_DIR / f"{uid}_uber_session.json"


def load_user_data(uid: str) -> Dict[str, Any]:
    """Load user data from file."""
    user_file = get_user_file(uid)
    if user_file.exists():
        with open(user_file, "r") as f:
            return json.load(f)
    return {
        "uid": uid,
        "uber_authenticated": False,
        "auth_status": "not_authenticated",
        "last_booking": None,
        "remember_device": False,
        "uber_email": None,
        "uber_password": None,
        "created_at": datetime.utcnow().isoformat(),
    }


def save_user_data(uid: str, data: Dict[str, Any]):
    """Save user data to file."""
    ensure_dirs()
    user_file = get_user_file(uid)
    with open(user_file, "w") as f:
        json.dump(data, f, indent=2)


def update_user_status(uid: str, auth_status: str, authenticated: bool = None):
    """Update user authentication status."""
    data = load_user_data(uid)
    data["auth_status"] = auth_status
    if authenticated is not None:
        data["uber_authenticated"] = authenticated
    data["updated_at"] = datetime.utcnow().isoformat()
    save_user_data(uid, data)


def save_session(uid: str, session_data: Dict[str, Any]):
    """Save browser session to file."""
    ensure_dirs()
    session_file = get_session_file(uid)
    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)


def load_session(uid: str) -> Optional[Dict[str, Any]]:
    """Load browser session from file."""
    session_file = get_session_file(uid)
    if session_file.exists():
        with open(session_file, "r") as f:
            return json.load(f)
    return None


def delete_session(uid: str):
    """Delete user session."""
    session_file = get_session_file(uid)
    if session_file.exists():
        session_file.unlink()


def record_booking(uid: str, destination: str, driver_name: str = None, eta: str = None):
    """Record a completed booking."""
    data = load_user_data(uid)
    data["last_booking"] = {
        "destination": destination,
        "driver_name": driver_name,
        "eta": eta,
        "timestamp": datetime.utcnow().isoformat(),
    }
    save_user_data(uid, data)


def set_remember_device(uid: str, remember: bool):
    """Set remember device preference."""
    data = load_user_data(uid)
    data["remember_device"] = remember
    save_user_data(uid, data)


def save_uber_credentials(uid: str, email: str, password: str):
    """Save Uber credentials for auto re-authentication."""
    data = load_user_data(uid)
    data["uber_email"] = email
    data["uber_password"] = password
    save_user_data(uid, data)


def get_uber_credentials(uid: str) -> tuple[Optional[str], Optional[str]]:
    """Get saved Uber credentials."""
    data = load_user_data(uid)
    return data.get("uber_email"), data.get("uber_password")
