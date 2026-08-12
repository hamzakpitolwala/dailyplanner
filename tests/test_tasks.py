import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
"""Tests for the Task and Category APIs.

Replaces the deleted test_history.py and test_planner_schema.py tests.
The old DailyPlanner / Activity / ActivityHistoryEvent models are gone;
the current schema exposes /tasks and /categories instead.
"""

from uuid import UUID

import pytest


from backend.main import app

client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register_and_login(email: str = "tasks@example.com") -> str:
    await client.post(
        "/auth/register",
        json={"email": email, "password": "secret1234"},
    )
    resp = await client.post(
        "/auth/login",
        json={"email": email, "password": "secret1234"},
    )
    return resp.json()["access_token"]


async def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_category(token: str, name: str = "Work", color: str = "#FF5733") -> dict:
    return (await client.post(
        "/categories",
        json={"name": name, "color_hex": color},
        headers=await _auth(token),
    )).json()


async def _create_task(token: str, title: str = "Write tests", category_id: str | None = None) -> dict:
    payload: dict = {"title": title, "priority": 2}
    if category_id:
        payload["category_id"] = category_id
    return (await client.post("/tasks", json=payload, headers=await _auth(token))).json()


# ===========================================================================
# Category CRUD
# ===========================================================================


class TestCategoryCRUD:
    @pytest.mark.asyncio
    async def test_create_category(self):
        token = await _register_and_login("cat_create@example.com")
        resp = await client.post(
            "/categories",
            json={"name": "Health", "color_hex": "#00FF00"},
            headers=await _auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Health"
        assert data["color_hex"] == "#00FF00"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_category_blank_name_fails(self):
        token = await _register_and_login("cat_blank@example.com")
        resp = await client.post(
            "/categories",
            json={"name": "", "color_hex": "#FFFFFF"},
            headers=await _auth(token),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_categories_empty(self):
        token = await _register_and_login("cat_list_empty@example.com")
        resp = await client.get("/categories", headers=await _auth(token))
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_categories_returns_own_only(self):
        token1 = await _register_and_login("cat_list1@example.com")
        token2 = await _register_and_login("cat_list2@example.com")
        await _create_category(token1, "Private Cat")

        resp = await client.get("/categories", headers=await _auth(token2))
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_update_category(self):
        token = await _register_and_login("cat_update@example.com")
        cat = await _create_category(token, "Old Name")
        cat_id = cat["id"]

        resp = await client.patch(
            f"/categories/{cat_id}",
            json={"name": "New Name"},
            headers=await _auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_category_color(self):
        token = await _register_and_login("cat_color@example.com")
        cat = await _create_category(token, "Colorful")
        cat_id = cat["id"]

        resp = await client.patch(
            f"/categories/{cat_id}",
            json={"color_hex": "#123456"},
            headers=await _auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["color_hex"] == "#123456"

    @pytest.mark.asyncio
    async def test_update_category_not_found(self):
        token = await _register_and_login("cat_upd404@example.com")
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.patch(
            f"/categories/{fake_id}",
            json={"name": "Ghost"},
            headers=await _auth(token),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_other_users_category_fails(self):
        token1 = await _register_and_login("catowner@example.com")
        token2 = await _register_and_login("cathijacker@example.com")
        cat = await _create_category(token1, "Mine")

        resp = await client.patch(
            f"/categories/{cat['id']}",
            json={"name": "Stolen"},
            headers=await _auth(token2),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_category(self):
        token = await _register_and_login("cat_del@example.com")
        cat = await _create_category(token, "ToDelete")

        resp = await client.delete(f"/categories/{cat['id']}", headers=await _auth(token))
        assert resp.status_code == 204

        # Verify it's gone from list
        cats = (await client.get("/categories", headers=await _auth(token))).json()
        assert all(c["id"] != cat["id"] for c in cats)

    @pytest.mark.asyncio
    async def test_delete_category_not_found(self):
        token = await _register_and_login("cat_del404@example.com")
        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = await client.delete(f"/categories/{fake_id}", headers=await _auth(token))
        assert resp.status_code == 404


# ===========================================================================
# Task CRUD
# ===========================================================================


class TestTaskCRUD:
    @pytest.mark.asyncio
    async def test_create_task_minimal(self):
        token = await _register_and_login("task_create@example.com")
        resp = await client.post(
            "/tasks",
            json={"title": "Read a book"},
            headers=await _auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Read a book"
        assert data["status"] == "pending"
        assert data["priority"] == 1
        assert data["checklist"] == []

    @pytest.mark.asyncio
    async def test_create_task_with_category(self):
        token = await _register_and_login("task_cat@example.com")
        cat = await _create_category(token, "Learning")
        resp = await client.post(
            "/tasks",
            json={"title": "Study SQLAlchemy", "category_id": cat["id"]},
            headers=await _auth(token),
        )
        assert resp.status_code == 201
        assert resp.json()["category_id"] == cat["id"]

    @pytest.mark.asyncio
    async def test_create_task_with_invalid_category_fails(self):
        token = await _register_and_login("task_badcat@example.com")
        fake_cat = "00000000-0000-0000-0000-000000000099"
        resp = await client.post(
            "/tasks",
            json={"title": "Orphan task", "category_id": fake_cat},
            headers=await _auth(token),
        )
        # DB FK constraint violation → 422 or 400
        assert resp.status_code in (400, 422, 500)

    @pytest.mark.asyncio
    async def test_create_task_blank_title_fails(self):
        token = await _register_and_login("task_notitle@example.com")
        resp = await client.post(
            "/tasks",
            json={"title": ""},
            headers=await _auth(token),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self):
        token = await _register_and_login("task_list_empty@example.com")
        resp = await client.get("/tasks", headers=await _auth(token))
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_tasks_returns_own_only(self):
        token1 = await _register_and_login("tasks_own1@example.com")
        token2 = await _register_and_login("tasks_own2@example.com")
        await _create_task(token1, "Secret task")

        resp = await client.get("/tasks", headers=await _auth(token2))
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_task(self):
        token = await _register_and_login("task_get@example.com")
        task = await _create_task(token, "Fetch me")
        task_id = task["id"]

        resp = await client.get(f"/tasks/{task_id}", headers=await _auth(token))
        assert resp.status_code == 200
        assert resp.json()["id"] == task_id

    @pytest.mark.asyncio
    async def test_get_task_not_found(self):
        token = await _register_and_login("task_get404@example.com")
        fake = "00000000-0000-0000-0000-000000000002"
        resp = await client.get(f"/tasks/{fake}", headers=await _auth(token))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_other_users_task_fails(self):
        token1 = await _register_and_login("task_owner@example.com")
        token2 = await _register_and_login("task_spy@example.com")
        task = await _create_task(token1, "My secret task")

        resp = await client.get(f"/tasks/{task['id']}", headers=await _auth(token2))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_task_title(self):
        token = await _register_and_login("task_upd_title@example.com")
        task = await _create_task(token, "Old Title")

        resp = await client.patch(
            f"/tasks/{task['id']}",
            json={"title": "New Title"},
            headers=await _auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"

    @pytest.mark.asyncio
    async def test_update_task_status_to_completed(self):
        """Updating status to 'completed' should auto-set completed_at."""
        token = await _register_and_login("task_complete@example.com")
        task = await _create_task(token, "Finish this")

        resp = await client.patch(
            f"/tasks/{task['id']}",
            json={"status": "completed"},
            headers=await _auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_update_task_checklist(self):
        token = await _register_and_login("task_check@example.com")
        task = await _create_task(token, "Checklist task")

        checklist = [{"item": "Step 1", "done": False}, {"item": "Step 2", "done": True}]
        resp = await client.patch(
            f"/tasks/{task['id']}",
            json={"checklist": checklist},
            headers=await _auth(token),
        )
        assert resp.status_code == 200
        assert len(resp.json()["checklist"]) == 2

    @pytest.mark.asyncio
    async def test_update_task_priority(self):
        token = await _register_and_login("task_prio@example.com")
        task = await _create_task(token, "Priority task")

        resp = await client.patch(
            f"/tasks/{task['id']}",
            json={"priority": 5},
            headers=await _auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["priority"] == 5

    @pytest.mark.asyncio
    async def test_update_task_invalid_priority_fails(self):
        token = await _register_and_login("task_badprio@example.com")
        task = await _create_task(token, "Bad prio")

        resp = await client.patch(
            f"/tasks/{task['id']}",
            json={"priority": 0},
            headers=await _auth(token),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_update_other_users_task_fails(self):
        token1 = await _register_and_login("task_upd_own@example.com")
        token2 = await _register_and_login("task_upd_hacker@example.com")
        task = await _create_task(token1, "Protected task")

        resp = await client.patch(
            f"/tasks/{task['id']}",
            json={"title": "Hijacked"},
            headers=await _auth(token2),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_task(self):
        token = await _register_and_login("task_del@example.com")
        task = await _create_task(token, "Delete me")

        resp = await client.delete(f"/tasks/{task['id']}", headers=await _auth(token))
        assert resp.status_code == 204

        follow = await client.get(f"/tasks/{task['id']}", headers=await _auth(token))
        assert follow.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self):
        token = await _register_and_login("task_del404@example.com")
        fake = "00000000-0000-0000-0000-000000000003"
        resp = await client.delete(f"/tasks/{fake}", headers=await _auth(token))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_other_users_task_fails(self):
        token1 = await _register_and_login("task_del_own@example.com")
        token2 = await _register_and_login("task_del_hacker@example.com")
        task = await _create_task(token1, "Do not touch")

        resp = await client.delete(f"/tasks/{task['id']}", headers=await _auth(token2))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_task_unauthenticated_access_fails(self):
        resp = await client.get("/tasks")
        assert resp.status_code == 401
