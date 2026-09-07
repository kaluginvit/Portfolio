"""
Meaningful tests for Mini CRM API.
Uses in-memory SQLite via conftest.py fixture — no external deps required.
"""


# ─────────────────────────── Clients ────────────────────────────

class TestClients:
    def test_create_client_minimal(self, client):
        r = client.post("/clients", json={"name": "Минимальный Клиент"})
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Минимальный Клиент"
        assert data["status"] == "active"
        assert "id" in data and "created_at" in data

    def test_create_client_full(self, client):
        r = client.post("/clients", json={
            "name": "Полный Клиент",
            "email": "full@example.com",
            "phone": "+79009999999",
            "company": "ООО Пример",
            "status": "active",
        })
        assert r.status_code == 201
        assert r.json()["email"] == "full@example.com"

    def test_create_client_invalid_email(self, client):
        r = client.post("/clients", json={"name": "Bad Email", "email": "not-an-email"})
        assert r.status_code == 422
        body = r.json()
        assert body["code"] == "validation_error"

    def test_create_client_empty_name(self, client):
        r = client.post("/clients", json={"name": ""})
        assert r.status_code == 422

    def test_get_client_not_found(self, client):
        r = client.get("/clients/99999")
        assert r.status_code == 404
        assert r.json()["code"] == "not_found"

    def test_get_client_ok(self, client):
        cid = client.post("/clients", json={"name": "Найди Меня"}).json()["id"]
        r = client.get(f"/clients/{cid}")
        assert r.status_code == 200
        assert r.json()["name"] == "Найди Меня"

    def test_update_client(self, client):
        cid = client.post("/clients", json={"name": "До"}).json()["id"]
        r = client.patch(f"/clients/{cid}", json={"name": "После", "status": "archived"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "После"
        assert data["status"] == "archived"

    def test_update_client_not_found(self, client):
        r = client.patch("/clients/88888", json={"name": "noop"})
        assert r.status_code == 404

    def test_delete_client(self, client):
        cid = client.post("/clients", json={"name": "Удали Меня"}).json()["id"]
        r = client.delete(f"/clients/{cid}")
        assert r.status_code == 204
        assert client.get(f"/clients/{cid}").status_code == 404

    def test_list_clients_pagination(self, client):
        for i in range(5):
            client.post("/clients", json={"name": f"Клиент {i}"})
        r = client.get("/clients", params={"skip": 0, "limit": 3})
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 5
        assert len(body["items"]) == 3

    def test_list_clients_search(self, client):
        client.post("/clients", json={"name": "Иванов Иван", "company": "АльфаТест"})
        client.post("/clients", json={"name": "Петров Петр"})
        r = client.get("/clients", params={"q": "АльфаТест"})
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_list_clients_filter_status(self, client):
        client.post("/clients", json={"name": "Активный", "status": "active"})
        cid = client.post("/clients", json={"name": "Архивный"}).json()["id"]
        client.patch(f"/clients/{cid}", json={"status": "archived"})
        r = client.get("/clients", params={"status": "archived"})
        assert r.status_code == 200
        assert all(c["status"] == "archived" for c in r.json()["items"])

    def test_invalid_status_value(self, client):
        r = client.post("/clients", json={"name": "Bad Status", "status": "invalid_status"})
        assert r.status_code == 422


# ─────────────────────────── Deals ────────────────────────────

class TestDeals:
    def _create_client(self, client):
        return client.post("/clients", json={"name": "Клиент для Сделок"}).json()["id"]

    def test_create_deal_minimal(self, client):
        r = client.post("/deals", json={"title": "Сделка Тест"})
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "Сделка Тест"
        assert data["stage"] == "lead"

    def test_create_deal_with_client(self, client):
        cid = self._create_client(client)
        r = client.post("/deals", json={"title": "Связанная сделка", "client_id": cid, "amount": 150000})
        assert r.status_code == 201
        assert r.json()["client_id"] == cid
        assert r.json()["amount"] == 150000

    def test_create_deal_invalid_client(self, client):
        r = client.post("/deals", json={"title": "Сделка", "client_id": 99999})
        assert r.status_code == 422
        assert r.json()["code"] == "validation"

    def test_create_deal_negative_amount(self, client):
        r = client.post("/deals", json={"title": "Отрицательная сумма", "amount": -1})
        assert r.status_code == 422

    def test_get_deal_not_found(self, client):
        r = client.get("/deals/99999")
        assert r.status_code == 404

    def test_update_deal_stage(self, client):
        did = client.post("/deals", json={"title": "Сделка"}).json()["id"]
        r = client.patch(f"/deals/{did}", json={"stage": "won"})
        assert r.status_code == 200
        assert r.json()["stage"] == "won"

    def test_delete_deal(self, client):
        did = client.post("/deals", json={"title": "Удалить"}).json()["id"]
        assert client.delete(f"/deals/{did}").status_code == 204
        assert client.get(f"/deals/{did}").status_code == 404


# ─────────────────────────── Tasks ────────────────────────────

class TestTasks:
    def test_create_task(self, client):
        r = client.post("/tasks", json={"title": "Позвонить клиенту", "priority": "high"})
        assert r.status_code == 201
        data = r.json()
        assert data["priority"] == "high"
        assert data["done"] is False

    def test_mark_task_done(self, client):
        tid = client.post("/tasks", json={"title": "Задача"}).json()["id"]
        r = client.patch(f"/tasks/{tid}", json={"done": True})
        assert r.status_code == 200
        assert r.json()["done"] is True

    def test_create_task_empty_title(self, client):
        r = client.post("/tasks", json={"title": ""})
        assert r.status_code == 422

    def test_get_task_not_found(self, client):
        r = client.get("/tasks/99999")
        assert r.status_code == 404


# ─────────────────────────── Error format ────────────────────────────

class TestErrorFormat:
    """Verify error responses follow the documented ApiError schema."""

    def test_404_has_code_and_message(self, client):
        r = client.get("/clients/99999")
        body = r.json()
        assert "code" in body
        assert "message" in body

    def test_422_has_code_validation_error(self, client):
        r = client.post("/clients", json={"name": ""})
        body = r.json()
        assert body["code"] == "validation_error"
        assert "detail" in body
