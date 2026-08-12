import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
"""Integration tests for the Templates API.

Covers:
- Template CRUD (create, list, get, update, delete)
- Template Task CRUD (create, update, delete)
- Template instantiation → /apply endpoint creates real Tasks
- Ownership isolation (user A cannot touch user B's templates)

Replaces the old test_planner_schema.py which tested deleted models.
"""

from datetime import datetime, timezone

import pytest


from backend.main import app

client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register_and_login(email: str = "tmpl@example.com") -> str:
    await client.post("/auth/register", json={"email": email, "password": "secret1234"})
    resp = await client.post("/auth/login", json={"email": email, "password": "secret1234"})
    return resp.json()["access_token"]


async def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_template(
    token: str,
    name: str = "Morning Routine",
    description: str | None = "Daily morning tasks",
    tasks: list | None = None,
) -> dict:
    payload: dict = {"name": name}
    if description is not None:
        payload["description"] = description
    payload["template_tasks"] = tasks or []
    return (await client.post("/templates", json=payload, headers=await _auth(token))).json()


async def _create_template_task(token: str, template_id: str, title: str = "New Task") -> dict:
    return (await client.post(
        f"/templates/{template_id}/tasks",
        json={"title": title, "priority": 1},
        headers=await _auth(token),
    )).json()


# ===========================================================================
# Template CRUD
# ===========================================================================


class TestTemplateCRUD:
    @pytest.mark.asyncio
    async def test_create_template_minimal(self):
        token = await _register_and_login("tmpl_create@example.com")
        resp = await client.post(
            "/templates",
            json={"name": "Simple Template", "template_tasks": []},
            headers=await _auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Simple Template"
        assert data["template_tasks"] == []
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_template_with_nested_tasks(self):
        token = await _register_and_login("tmpl_nested@example.com")
        resp = await client.post(
            "/templates",
            json={
                "name": "Full Day",
                "template_tasks": [
                    {"title": "Morning run", "priority": 1, "relative_day_offset": 0},
                    {"title": "Lunch break", "priority": 1, "relative_day_offset": 0},
                ],
            },
            headers=await _auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["template_tasks"]) == 2
        titles = {t["title"] for t in data["template_tasks"]}
        assert titles == {"Morning run", "Lunch break"}

    @pytest.mark.asyncio
    async def test_create_template_blank_name_fails(self):
        token = await _register_and_login("tmpl_noname@example.com")
        resp = await client.post(
            "/templates",
            json={"name": "", "template_tasks": []},
            headers=await _auth(token),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_templates_empty(self):
        token = await _register_and_login("tmpl_list_empty@example.com")
        resp = await client.get("/templates", headers=await _auth(token))
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_templates_returns_own_only(self):
        token1 = await _register_and_login("tmpl_own1@example.com")
        token2 = await _register_and_login("tmpl_own2@example.com")
        await _create_template(token1, name="Private Template")

        resp = await client.get("/templates", headers=await _auth(token2))
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_template(self):
        token = await _register_and_login("tmpl_get@example.com")
        tmpl = await _create_template(token, name="Get Me")
        tmpl_id = tmpl["id"]

        resp = await client.get(f"/templates/{tmpl_id}", headers=await _auth(token))
        assert resp.status_code == 200
        assert resp.json()["id"] == tmpl_id

    @pytest.mark.asyncio
    async def test_get_template_not_found(self):
        token = await _register_and_login("tmpl_get404@example.com")
        fake = "00000000-0000-0000-0000-000000000010"
        resp = await client.get(f"/templates/{fake}", headers=await _auth(token))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_other_users_template_fails(self):
        token1 = await _register_and_login("tmpl_spy_owner@example.com")
        token2 = await _register_and_login("tmpl_spy_spy@example.com")
        tmpl = await _create_template(token1, name="Owner's Template")

        resp = await client.get(f"/templates/{tmpl['id']}", headers=await _auth(token2))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_template_name(self):
        token = await _register_and_login("tmpl_upd@example.com")
        tmpl = await _create_template(token, name="Old Name")

        resp = await client.patch(
            f"/templates/{tmpl['id']}",
            json={"name": "New Name"},
            headers=await _auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_template_not_found(self):
        token = await _register_and_login("tmpl_upd404@example.com")
        fake = "00000000-0000-0000-0000-000000000011"
        resp = await client.patch(
            f"/templates/{fake}",
            json={"name": "Ghost"},
            headers=await _auth(token),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_other_users_template_fails(self):
        token1 = await _register_and_login("tmpl_upd_own@example.com")
        token2 = await _register_and_login("tmpl_upd_hack@example.com")
        tmpl = await _create_template(token1, name="Protected")

        resp = await client.patch(
            f"/templates/{tmpl['id']}",
            json={"name": "Stolen"},
            headers=await _auth(token2),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_template(self):
        token = await _register_and_login("tmpl_del@example.com")
        tmpl = await _create_template(token, name="Delete Me")

        resp = await client.delete(f"/templates/{tmpl['id']}", headers=await _auth(token))
        assert resp.status_code == 204

        follow = await client.get(f"/templates/{tmpl['id']}", headers=await _auth(token))
        assert follow.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_template_not_found(self):
        token = await _register_and_login("tmpl_del404@example.com")
        fake = "00000000-0000-0000-0000-000000000012"
        resp = await client.delete(f"/templates/{fake}", headers=await _auth(token))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_other_users_template_fails(self):
        token1 = await _register_and_login("tmpl_del_own@example.com")
        token2 = await _register_and_login("tmpl_del_hack@example.com")
        tmpl = await _create_template(token1)

        resp = await client.delete(f"/templates/{tmpl['id']}", headers=await _auth(token2))
        assert resp.status_code == 404


# ===========================================================================
# Template Task CRUD
# ===========================================================================


class TestTemplateTaskCRUD:
    @pytest.mark.asyncio
    async def test_create_template_task(self):
        token = await _register_and_login("ttask_create@example.com")
        tmpl = await _create_template(token, name="Base Template")

        resp = await client.post(
            f"/templates/{tmpl['id']}/tasks",
            json={"title": "Morning run", "priority": 2, "relative_day_offset": 0},
            headers=await _auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Morning run"
        assert data["template_id"] == tmpl["id"]

    @pytest.mark.asyncio
    async def test_create_template_task_with_offset(self):
        token = await _register_and_login("ttask_offset@example.com")
        tmpl = await _create_template(token, name="Multi-Day")

        resp = await client.post(
            f"/templates/{tmpl['id']}/tasks",
            json={"title": "Day 3 task", "relative_day_offset": 2},
            headers=await _auth(token),
        )
        assert resp.status_code == 201
        assert resp.json()["relative_day_offset"] == 2

    @pytest.mark.asyncio
    async def test_create_template_task_on_nonexistent_template(self):
        token = await _register_and_login("ttask_404@example.com")
        fake = "00000000-0000-0000-0000-000000000020"
        resp = await client.post(
            f"/templates/{fake}/tasks",
            json={"title": "Ghost task"},
            headers=await _auth(token),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_template_task_on_other_users_template_fails(self):
        token1 = await _register_and_login("ttask_own@example.com")
        token2 = await _register_and_login("ttask_hack@example.com")
        tmpl = await _create_template(token1, name="Private")

        resp = await client.post(
            f"/templates/{tmpl['id']}/tasks",
            json={"title": "Injected task"},
            headers=await _auth(token2),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_template_task(self):
        token = await _register_and_login("ttask_upd@example.com")
        tmpl = await _create_template(token, name="Updateable")
        task = await _create_template_task(token, tmpl["id"], "Old Task Title")

        resp = await client.patch(
            f"/templates/{tmpl['id']}/tasks/{task['id']}",
            json={"title": "New Task Title", "priority": 3},
            headers=await _auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "New Task Title"
        assert data["priority"] == 3

    @pytest.mark.asyncio
    async def test_update_template_task_partial(self):
        token = await _register_and_login("ttask_upd_partial@example.com")
        tmpl = await _create_template(token, name="Partial update")
        task = await _create_template_task(token, tmpl["id"], "Keep title")

        resp = await client.patch(
            f"/templates/{tmpl['id']}/tasks/{task['id']}",
            json={"priority": 5},
            headers=await _auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Keep title"
        assert data["priority"] == 5

    @pytest.mark.asyncio
    async def test_update_template_task_not_found(self):
        token = await _register_and_login("ttask_upd404@example.com")
        tmpl = await _create_template(token)
        fake_task = "00000000-0000-0000-0000-000000000021"

        resp = await client.patch(
            f"/templates/{tmpl['id']}/tasks/{fake_task}",
            json={"title": "Ghost"},
            headers=await _auth(token),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_template_task(self):
        token = await _register_and_login("ttask_del@example.com")
        tmpl = await _create_template(token, name="Del tasks")
        task = await _create_template_task(token, tmpl["id"], "Removable")

        resp = await client.delete(
            f"/templates/{tmpl['id']}/tasks/{task['id']}",
            headers=await _auth(token),
        )
        assert resp.status_code == 204

        # Template still exists but task is gone
        tmpl_resp = (await client.get(f"/templates/{tmpl['id']}", headers=await _auth(token))).json()
        task_ids = [t["id"] for t in tmpl_resp["template_tasks"]]
        assert task["id"] not in task_ids

    @pytest.mark.asyncio
    async def test_delete_template_task_not_found(self):
        token = await _register_and_login("ttask_del404@example.com")
        tmpl = await _create_template(token)
        fake_task = "00000000-0000-0000-0000-000000000022"

        resp = await client.delete(
            f"/templates/{tmpl['id']}/tasks/{fake_task}",
            headers=await _auth(token),
        )
        assert resp.status_code == 404


# ===========================================================================
# Template Instantiation (/apply)
# ===========================================================================


class TestTemplateApply:
    @pytest.mark.asyncio
    async def test_apply_creates_tasks(self):
        token = await _register_and_login("tmpl_apply@example.com")
        tmpl = await _create_template(
            token,
            name="Apply Test",
            tasks=[
                {"title": "Task A", "relative_day_offset": 0},
                {"title": "Task B", "relative_day_offset": 1},
            ],
        )
        target_date = "2025-08-01T08:00:00"
        resp = await client.post(
            f"/templates/{tmpl['id']}/apply",
            params={"target_date": target_date},
            headers=await _auth(token),
        )
        assert resp.status_code == 201
        tasks = resp.json()
        assert len(tasks) == 2
        titles = {t["title"] for t in tasks}
        assert titles == {"Task A", "Task B"}
        # Task B should be offset by 1 day
        task_b = next(t for t in tasks if t["title"] == "Task B")
        assert "2025-08-02" in task_b["due_date"]

    @pytest.mark.asyncio
    async def test_apply_nonexistent_template_fails(self):
        token = await _register_and_login("tmpl_apply404@example.com")
        fake = "00000000-0000-0000-0000-000000000030"
        resp = await client.post(
            f"/templates/{fake}/apply",
            params={"target_date": "2025-08-01T00:00:00"},
            headers=await _auth(token),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_apply_other_users_template_fails(self):
        token1 = await _register_and_login("tmpl_apply_own@example.com")
        token2 = await _register_and_login("tmpl_apply_hack@example.com")
        tmpl = await _create_template(token1, name="Private")

        resp = await client.post(
            f"/templates/{tmpl['id']}/apply",
            params={"target_date": "2025-08-01T00:00:00"},
            headers=await _auth(token2),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_apply_sets_source_template_name(self):
        token = await _register_and_login("tmpl_source@example.com")
        tmpl = await _create_template(
            token,
            name="Named Template",
            tasks=[{"title": "Only task", "relative_day_offset": 0}],
        )
        resp = await client.post(
            f"/templates/{tmpl['id']}/apply",
            params={"target_date": "2025-09-01T09:00:00"},
            headers=await _auth(token),
        )
        assert resp.status_code == 201
        assert resp.json()[0]["source_template_name"] == "Named Template"
