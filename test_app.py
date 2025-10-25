"""
Test suite for Omi Uber App
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app
from simple_storage import (
    load_user_data,
    save_user_data,
    load_session,
    save_session,
    delete_session,
)
from ride_detector import is_trigger_phrase, extract_destination

client = TestClient(app)


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ============================================================================
# HOME PAGE TESTS
# ============================================================================


def test_home_page():
    """Test home page loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Omi Uber" in response.text
    assert "Connect Uber Account" in response.text


def test_home_page_with_uid():
    """Test home page with user ID."""
    response = client.get("/?uid=test_user")
    assert response.status_code == 200
    assert "Omi Uber" in response.text


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================


def test_auth_page():
    """Test auth page loads."""
    response = client.get("/auth?uid=test_user")
    assert response.status_code == 200
    assert "Authenticating" in response.text


def test_auth_status_not_authenticated():
    """Test auth status for unauthenticated user."""
    response = client.get("/auth-status?uid=new_user")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_authenticated"


def test_submit_2fa_code_invalid_format():
    """Test 2FA code submission with invalid format."""
    response = client.post(
        "/submit-2fa-code",
        json={"uid": "test_user", "code": "12"}  # Too short
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False


def test_submit_2fa_code_valid_format():
    """Test 2FA code submission with valid format."""
    response = client.post(
        "/submit-2fa-code",
        json={"uid": "test_user", "code": "123456"}
    )
    assert response.status_code == 200
    data = response.json()
    # Will fail because no active session, but format is valid
    assert "success" in data


def test_setup_completed_not_authenticated():
    """Test setup completed check for unauthenticated user."""
    response = client.get("/setup-completed?uid=new_user")
    assert response.status_code == 200
    data = response.json()
    assert data["is_setup_completed"] is False


# ============================================================================
# WEBHOOK TESTS
# ============================================================================


def test_webhook_no_trigger():
    """Test webhook with no trigger phrase."""
    response = client.post(
        "/webhook",
        json={
            "uid": "test_user",
            "segments": [
                {"text": "hello world", "speaker": "user"}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["booked"] is False


def test_webhook_trigger_no_destination():
    """Test webhook with trigger but no destination."""
    response = client.post(
        "/webhook",
        json={
            "uid": "test_user",
            "segments": [
                {"text": "book an uber", "speaker": "user"}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["booked"] is False


def test_webhook_not_authenticated():
    """Test webhook when user not authenticated."""
    response = client.post(
        "/webhook",
        json={
            "uid": "new_user",
            "segments": [
                {"text": "book an uber to san francisco", "speaker": "user"}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["booked"] is False
    assert "authenticate" in data["message"].lower()


# ============================================================================
# STORAGE TESTS
# ============================================================================


def test_load_new_user_data():
    """Test loading data for new user."""
    data = load_user_data("new_test_user")
    assert data["uid"] == "new_test_user"
    assert data["uber_authenticated"] is False
    assert data["auth_status"] == "not_authenticated"


def test_save_and_load_user_data():
    """Test saving and loading user data."""
    uid = "test_save_user"
    original_data = {
        "uid": uid,
        "uber_authenticated": True,
        "auth_status": "completed",
        "last_booking": "SFO",
    }
    save_user_data(uid, original_data)
    loaded_data = load_user_data(uid)
    assert loaded_data["uber_authenticated"] is True
    assert loaded_data["auth_status"] == "completed"


def test_session_storage():
    """Test session save and load."""
    uid = "test_session_user"
    session_data = {
        "cookies": [{"name": "test", "value": "value"}],
        "localStorage": [{"name": "key", "value": "value"}],
    }
    save_session(uid, session_data)
    loaded_session = load_session(uid)
    assert loaded_session is not None
    assert loaded_session["cookies"] == session_data["cookies"]


def test_delete_session():
    """Test session deletion."""
    uid = "test_delete_user"
    session_data = {"cookies": []}
    save_session(uid, session_data)
    assert load_session(uid) is not None
    delete_session(uid)
    assert load_session(uid) is None


# ============================================================================
# RIDE DETECTOR TESTS
# ============================================================================


def test_trigger_phrase_book_uber():
    """Test trigger detection for 'book an uber'."""
    assert is_trigger_phrase("book an uber to downtown") is True


def test_trigger_phrase_get_ride():
    """Test trigger detection for 'get me a ride'."""
    assert is_trigger_phrase("get me a ride to the airport") is True


def test_trigger_phrase_call_uber():
    """Test trigger detection for 'call an uber'."""
    assert is_trigger_phrase("call an uber to my house") is True


def test_trigger_phrase_request_uber():
    """Test trigger detection for 'request an uber'."""
    assert is_trigger_phrase("request an uber to work") is True


def test_trigger_phrase_order_uber():
    """Test trigger detection for 'order an uber'."""
    assert is_trigger_phrase("order an uber to the station") is True


def test_no_trigger_phrase():
    """Test no trigger detection."""
    assert is_trigger_phrase("what is the weather today") is False


def test_trigger_case_insensitive():
    """Test trigger detection is case insensitive."""
    assert is_trigger_phrase("BOOK AN UBER TO DOWNTOWN") is True
    assert is_trigger_phrase("Book An Uber To Downtown") is True


@pytest.mark.asyncio
async def test_extract_destination():
    """Test destination extraction."""
    # Note: This requires OPENAI_API_KEY to be set
    # Skipping in CI/CD without API key
    import os
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    destination = extract_destination("book an uber to san francisco airport")
    assert destination is not None
    assert "san francisco" in destination.lower() or "sfo" in destination.lower()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_full_home_flow():
    """Test full flow from home page."""
    # Get home page
    response = client.get("/?uid=integration_test")
    assert response.status_code == 200

    # Check auth status
    response = client.get("/auth-status?uid=integration_test")
    assert response.status_code == 200
    assert response.json()["status"] == "not_authenticated"

    # Check setup not completed
    response = client.get("/setup-completed?uid=integration_test")
    assert response.status_code == 200
    assert response.json()["is_setup_completed"] is False


def test_error_handling_webhook():
    """Test webhook error handling."""
    response = client.post(
        "/webhook",
        json={
            "uid": "error_test",
            "segments": []  # Empty segments
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "booked" in data


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
