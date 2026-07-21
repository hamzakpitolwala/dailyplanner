"""Tests for the Task and Category APIs.

Replaces the deleted test_history.py and test_planner_schema.py tests.
The old DailyPlanner / Activity / ActivityHistoryEvent models are gone;
the current schema exposes /tasks and /categories instead.
"""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_login(email: str = "tasks@example.com") -> str:
    client.post(
        "/auth/register",
        json={"email": email, "password": "secret1234"},
    )
    resp = client.post(
        "/auth/login",
        json={"email": email, "password": "secret1234"},
    )
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_category(token: str, name: str = "Work", color: str = "#FF5733") -> dict:
    return client.post(
        "/categories",
        json={"name": name, "color_hex": color},
        headers=_auth(token),
    ).json()


def _create_task(token: str, title: str = "Write tests", category_id: str | None = None) -> dict:
    payload: dict = {"title": title, "priority": 2}
    if category_id:
        payload["category_id"] = category_id
    return client.post("/tasks", json=payload, headers=_auth(token)).json()


# ===========================================================================
# Category CRUD
# ===========================================================================


class TestCategoryCRUD:
    def test_create_category(self):
        token = _register_and_login("cat_create@example.com")
        resp = client.post(
            "/categories",
            json={"name": "Health", "color_hex": "#00FF00"},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Health"
        assert data["color_hex"] == "#00FF00"
        assert "id" in data

    def test_create_category_blank_name_fails(self):
        token = _register_and_login("cat_blank@example.com")
        resp = client.post(
            "/categories",
            json={"name": "", "color_hex": "#FFFFFF"},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_list_categories_empty(self):
        token = _register_and_login("cat_list_empty@example.com")
        resp = client.get("/categories", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_categories_returns_own_only(self):
        token1 = _register_and_login("cat_list1@example.com")
        token2 = _register_and_login("cat_list2@example.com")
        _create_category(token1, "Private Cat")

        resp = client.get("/categories", headers=_auth(token2))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_update_category(self):
        token = _register_and_login("cat_update@example.com")
        cat = _create_category(token, "Old Name")
        cat_id = cat["id"]

        resp = client.patch(
            f"/categories/{cat_id}",
            json={"name": "New Name"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_update_category_color(self):
        token = _register_and_login("cat_color@example.com")
        cat = _create_category(token, "Colorful")
        cat_id = cat["id"]

        resp = client.patch(
            f"/categories/{cat_id}",
            json={"color_hex": "#123456"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["color_hex"] == "#123456"

    def test_update_category_not_found(self):
        token = _register_and_login("cat_upd404@example.com")
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = client.patch(
            f"/categories/{fake_id}",
            json={"name": "Ghost"},
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_update_other_users_category_fails(self):
        token1 = _register_and_login("catowner@example.com")
        token2 = _register_and_login("cathijacker@example.com")
        cat = _create_category(token1, "Mine")

        resp = client.patch(
            f"/categories/{cat['id']}",
            json={"name": "Stolen"},
            headers=_auth(token2),
        )
        assert resp.status_code == 404

    def test_delete_category(self):
        token = _register_and_login("cat_del@example.com")
        cat = _create_category(token, "ToDelete")

        resp = client.delete(f"/categories/{cat['id']}", headers=_auth(token))
        assert resp.status_code == 204

        # Verify it's gone from list
        cats = client.get("/categories", headers=_auth(token)).json()
        assert all(c["id"] != cat["id"] for c in cats)

    def test_delete_category_not_found(self):
        token = _register_and_login("cat_del404@example.com")
        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = client.delete(f"/categories/{fake_id}", headers=_auth(token))
        assert resp.status_code == 404


# ===========================================================================
# Task CRUD
# ===========================================================================


class TestTaskCRUD:
    def test_create_task_minimal(self):
        token = _register_and_login("task_create@example.com")
        resp = client.post(
            "/tasks",
            json={"title": "Read a book"},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Read a book"
        assert data["status"] == "pending"
        assert data["priority"] == 1
        assert data["checklist"] == []

    def test_create_task_with_category(self):
        token = _register_and_login("task_cat@example.com")
        cat = _create_category(token, "Learning")
        resp = client.post(
            "/tasks",
            json={"title": "Study SQLAlchemy", "category_id": cat["id"]},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        assert resp.json()["category_id"] == cat["id"]

    def test_create_task_with_invalid_category_fails(self):
        token = _register_and_login("task_badcat@example.com")
        fake_cat = "00000000-0000-0000-0000-000000000099"
        resp = client.post(
            "/tasks",
            json={"title": "Orphan task", "category_id": fake_cat},
            headers=_auth(token),
        )
        # DB FK constraint violation → 422 or 400
        assert resp.status_code in (400, 422, 500)

    def test_create_task_blank_title_fails(self):
        token = _register_and_login("task_notitle@example.com")
        resp = client.post(
            "/tasks",
            json={"title": ""},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_list_tasks_empty(self):
        token = _register_and_login("task_list_empty@example.com")
        resp = client.get("/tasks", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_tasks_returns_own_only(self):
        token1 = _register_and_login("tasks_own1@example.com")
        token2 = _register_and_login("tasks_own2@example.com")
        _create_task(token1, "Secret task")

        resp = client.get("/tasks", headers=_auth(token2))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_task(self):
        token = _register_and_login("task_get@example.com")
        task = _create_task(token, "Fetch me")
        task_id = task["id"]

        resp = client.get(f"/tasks/{task_id}", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["id"] == task_id

    def test_get_task_not_found(self):
        token = _register_and_login("task_get404@example.com")
        fake = "00000000-0000-0000-0000-000000000002"
        resp = client.get(f"/tasks/{fake}", headers=_auth(token))
        assert resp.status_code == 404

    def test_get_other_users_task_fails(self):
        token1 = _register_and_login("task_owner@example.com")
        token2 = _register_and_login("task_spy@example.com")
        task = _create_task(token1, "My secret task")

        resp = client.get(f"/tasks/{task['id']}", headers=_auth(token2))
        assert resp.status_code == 404

    def test_update_task_title(self):
        token = _register_and_login("task_upd_title@example.com")
        task = _create_task(token, "Old Title")

        resp = client.patch(
            f"/tasks/{task['id']}",
            json={"title": "New Title"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"

    def test_update_task_status_to_completed(self):
        """Updating status to 'completed' should auto-set completed_at."""
        token = _register_and_login("task_complete@example.com")
        task = _create_task(token, "Finish this")

        resp = client.patch(
            f"/tasks/{task['id']}",
            json={"status": "completed"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_update_task_checklist(self):
        token = _register_and_login("task_check@example.com")
        task = _create_task(token, "Checklist task")

        checklist = [{"item": "Step 1", "done": False}, {"item": "Step 2", "done": True}]
        resp = client.patch(
            f"/tasks/{task['id']}",
            json={"checklist": checklist},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert len(resp.json()["checklist"]) == 2

    def test_update_task_priority(self):
        token = _register_and_login("task_prio@example.com")
        task = _create_task(token, "Priority task")

        resp = client.patch(
            f"/tasks/{task['id']}",
            json={"priority": 5},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["priority"] == 5

    def test_update_task_invalid_priority_fails(self):
        token = _register_and_login("task_badprio@example.com")
        task = _create_task(token, "Bad prio")

        resp = client.patch(
            f"/tasks/{task['id']}",
            json={"priority": 0},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_update_other_users_task_fails(self):
        token1 = _register_and_login("task_upd_own@example.com")
        token2 = _register_and_login("task_upd_hacker@example.com")
        task = _create_task(token1, "Protected task")

        resp = client.patch(
            f"/tasks/{task['id']}",
            json={"title": "Hijacked"},
            headers=_auth(token2),
        )
        assert resp.status_code == 404

    def test_delete_task(self):
        token = _register_and_login("task_del@example.com")
        task = _create_task(token, "Delete me")

        resp = client.delete(f"/tasks/{task['id']}", headers=_auth(token))
        assert resp.status_code == 204

        follow = client.get(f"/tasks/{task['id']}", headers=_auth(token))
        assert follow.status_code == 404

    def test_delete_task_not_found(self):
        token = _register_and_login("task_del404@example.com")
        fake = "00000000-0000-0000-0000-000000000003"
        resp = client.delete(f"/tasks/{fake}", headers=_auth(token))
        assert resp.status_code == 404

    def test_delete_other_users_task_fails(self):
        token1 = _register_and_login("task_del_own@example.com")
        token2 = _register_and_login("task_del_hacker@example.com")
        task = _create_task(token1, "Do not touch")

        resp = client.delete(f"/tasks/{task['id']}", headers=_auth(token2))
        assert resp.status_code == 404

    def test_task_unauthenticated_access_fails(self):
        resp = client.get("/tasks")
        assert resp.status_code == 401
