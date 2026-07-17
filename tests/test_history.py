"""Integration tests for the history and state machine flow (Phase 2.1)."""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_login(email: str = "history@example.com") -> str:
    """Register a user and return a valid JWT token."""
    client.post(
        "/auth/register",
        json={"email": email, "username": email.split("@")[0], "password": "secret1234"},
    )
    resp = client.post(
        "/auth/login",
        json={"email": email, "password": "secret1234"},
    )
    return resp.json()["access_token"]


def _create_planner_and_activity(
    token: str,
    *,
    requires_reason: bool = True,
    allows_alternate: bool = True,
) -> tuple[int, int]:
    """Create a planner for today and one activity, return (planner_id, activity_id)."""
    import datetime

    today = datetime.date.today().isoformat()
    planner = client.get(
        f"/planners/today?planner_date={today}",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    activity_resp = client.post(
        f"/planners/{planner['id']}/activities",
        json={
            "title": "Study Python",
            "category": "study",
            "start_time": "09:00",
            "end_time": "10:00",
            "policy": {
                "requires_reason": requires_reason,
                "allows_alternate": allows_alternate,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    activity = activity_resp.json()
    return planner["id"], activity["id"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_history_in_progress():
    """Transitioning to in_progress should succeed from planned."""
    token = _register_and_login("inprog@example.com")
    _planner_id, activity_id = _create_planner_and_activity(token)

    resp = client.post(
        f"/planners/activities/{activity_id}/history",
        json={"action_type": "status_change", "new_state": "in_progress"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    assert resp.json()["new_state"] == "in_progress"


def test_history_invalid_transition():
    """Transitioning directly from done to in_progress should fail."""
    token = _register_and_login("invalid@example.com")
    _planner_id, activity_id = _create_planner_and_activity(token)

    # First to done
    client.post(
        f"/planners/activities/{activity_id}/history",
        json={"action_type": "status_change", "new_state": "done"},
        headers=_auth_headers(token),
    )
    
    # Then to in_progress
    resp = client.post(
        f"/planners/activities/{activity_id}/history",
        json={"action_type": "status_change", "new_state": "in_progress"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400
    assert "invalid transition" in resp.json()["detail"].lower()


def test_history_done():
    """Marking an activity as done should succeed and update the activity status."""
    token = _register_and_login("done@example.com")
    _planner_id, activity_id = _create_planner_and_activity(token)

    resp = client.post(
        f"/planners/activities/{activity_id}/history",
        json={"action_type": "status_change", "new_state": "done", "notes": "Finished on time"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["new_state"] == "done"
    assert data["notes"] == "Finished on time"
    assert data["missed_reason"] is None
    assert data["alternate_activity"] is None


def test_history_partial():
    """Marking an activity as partial should succeed."""
    token = _register_and_login("partial@example.com")
    _planner_id, activity_id = _create_planner_and_activity(token)

    resp = client.post(
        f"/planners/activities/{activity_id}/history",
        json={"action_type": "status_change", "new_state": "partial", "notes": "Got halfway through"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    assert resp.json()["new_state"] == "partial"


def test_history_rescheduled():
    """Marking an activity as rescheduled should succeed."""
    token = _register_and_login("resched@example.com")
    _planner_id, activity_id = _create_planner_and_activity(token)

    resp = client.post(
        f"/planners/activities/{activity_id}/history",
        json={"action_type": "status_change", "new_state": "rescheduled"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    assert resp.json()["new_state"] == "rescheduled"


def test_history_not_done_with_reason():
    """not_done with a reason when policy requires it should succeed."""
    token = _register_and_login("reason@example.com")
    _planner_id, activity_id = _create_planner_and_activity(
        token, requires_reason=True
    )

    resp = client.post(
        f"/planners/activities/{activity_id}/history",
        json={
            "action_type": "status_change",
            "new_state": "not_done",
            "missed_reason": {
                "reason_code": "too_busy",
                "free_text": "Had an urgent meeting",
            },
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["new_state"] == "not_done"
    assert data["missed_reason"]["reason_code"] == "too_busy"
    assert data["missed_reason"]["free_text"] == "Had an urgent meeting"


def test_history_not_done_without_required_reason_fails():
    """not_done without a reason when policy.requires_reason=true should fail."""
    token = _register_and_login("noreason@example.com")
    _planner_id, activity_id = _create_planner_and_activity(
        token, requires_reason=True
    )

    resp = client.post(
        f"/planners/activities/{activity_id}/history",
        json={"action_type": "status_change", "new_state": "not_done"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400
    assert "reason is required" in resp.json()["detail"].lower()


def test_history_not_done_without_reason_ok_when_not_required():
    """not_done without a reason when policy.requires_reason=false should succeed."""
    token = _register_and_login("optionalreason@example.com")
    _planner_id, activity_id = _create_planner_and_activity(
        token, requires_reason=False
    )

    resp = client.post(
        f"/planners/activities/{activity_id}/history",
        json={"action_type": "status_change", "new_state": "not_done"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    assert resp.json()["missed_reason"] is None


def test_history_not_done_with_alternate():
    """not_done with an alternate activity when policy allows it."""
    token = _register_and_login("alt@example.com")
    _planner_id, activity_id = _create_planner_and_activity(
        token, requires_reason=False, allows_alternate=True
    )

    resp = client.post(
        f"/planners/activities/{activity_id}/history",
        json={
            "action_type": "status_change",
            "new_state": "not_done",
            "alternate_activity": {
                "description": "Doing some important work",
                "category": "work",
            },
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["alternate_activity"]["description"] == "Doing some important work"
    assert data["alternate_activity"]["category"] == "work"


def test_history_not_done_alternate_ignored_when_not_allowed():
    """Alternate activity should be ignored if policy.allows_alternate=false."""
    token = _register_and_login("noalt@example.com")
    _planner_id, activity_id = _create_planner_and_activity(
        token, requires_reason=False, allows_alternate=False
    )

    resp = client.post(
        f"/planners/activities/{activity_id}/history",
        json={
            "action_type": "status_change",
            "new_state": "not_done",
            "alternate_activity": {
                "description": "Tried to sneak this in",
            },
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    # alternate should be ignored because policy disallows it
    assert resp.json()["alternate_activity"] is None


def test_history_updates_activity_status():
    """After a history event, the activity's status should match the new state."""
    token = _register_and_login("statusupdate@example.com")
    planner_id, activity_id = _create_planner_and_activity(token)

    # Initially the status should be "planned"
    planner = client.get(
        f"/planners/{planner_id}",
        headers=_auth_headers(token),
    ).json()
    activity = [a for a in planner["activities"] if a["id"] == activity_id][0]
    assert activity["status"] == "planned"

    # Check in as done
    client.post(
        f"/planners/activities/{activity_id}/history",
        json={"action_type": "status_change", "new_state": "done"},
        headers=_auth_headers(token),
    )

    # Re-fetch and verify
    planner = client.get(
        f"/planners/{planner_id}",
        headers=_auth_headers(token),
    ).json()
    activity = [a for a in planner["activities"] if a["id"] == activity_id][0]
    assert activity["status"] == "done"


def test_list_history():
    """Listing history for an activity should return all of them."""
    token = _register_and_login("list@example.com")
    _planner_id, activity_id = _create_planner_and_activity(
        token, requires_reason=False
    )

    # Create two events
    client.post(
        f"/planners/activities/{activity_id}/history",
        json={"action_type": "status_change", "new_state": "partial"},
        headers=_auth_headers(token),
    )
    client.post(
        f"/planners/activities/{activity_id}/history",
        json={"action_type": "status_change", "new_state": "done"},
        headers=_auth_headers(token),
    )

    resp = client.get(
        f"/planners/activities/{activity_id}/history",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 2
    statuses = {c["new_state"] for c in history}
    assert statuses == {"partial", "done"}


def test_get_single_history():
    """Getting a single history event by id should work."""
    token = _register_and_login("single@example.com")
    _planner_id, activity_id = _create_planner_and_activity(token)

    create_resp = client.post(
        f"/planners/activities/{activity_id}/history",
        json={"action_type": "status_change", "new_state": "done"},
        headers=_auth_headers(token),
    )
    event_id = create_resp.json()["id"]

    resp = client.get(
        f"/planners/activities/history/{event_id}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == event_id


def test_history_activity_not_found():
    """History event on a non-existent activity should return 404."""
    token = _register_and_login("notfound@example.com")

    resp = client.post(
        "/planners/activities/99999/history",
        json={"action_type": "status_change", "new_state": "done"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 404


def test_history_reason_strips_for_non_not_done():
    """Reason/alternate should be silently stripped when state is not 'not_done'."""
    token = _register_and_login("strip@example.com")
    _planner_id, activity_id = _create_planner_and_activity(token)

    resp = client.post(
        f"/planners/activities/{activity_id}/history",
        json={
            "action_type": "status_change",
            "new_state": "done",
            "missed_reason": {"reason_code": "forgot"},
            "alternate_activity": {"description": "Something else"},
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["missed_reason"] is None
    assert data["alternate_activity"] is None
