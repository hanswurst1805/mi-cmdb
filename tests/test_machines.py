def test_create_machine(client):
    res = client.post("/api/v1/machines", json={
        "fqdn": "web01.example.com",
        "hostname": "web01",
        "os": "Ubuntu 22.04",
        "ram_gb": 16,
        "cpu_cores": 4,
        "owner": "ops-team",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["fqdn"] == "web01.example.com"
    assert data["status"] == "active"


def test_create_duplicate_fqdn(client):
    payload = {"fqdn": "db01.example.com", "hostname": "db01"}
    client.post("/api/v1/machines", json=payload)
    res = client.post("/api/v1/machines", json=payload)
    assert res.status_code == 409


def test_list_machines(client):
    client.post("/api/v1/machines", json={"fqdn": "app01.example.com", "hostname": "app01"})
    client.post("/api/v1/machines", json={"fqdn": "app02.example.com", "hostname": "app02"})
    res = client.get("/api/v1/machines")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_filter_by_status(client):
    client.post("/api/v1/machines", json={"fqdn": "a.example.com", "hostname": "a", "status": "active"})
    client.post("/api/v1/machines", json={"fqdn": "b.example.com", "hostname": "b", "status": "inactive"})
    res = client.get("/api/v1/machines?status=active")
    assert all(m["status"] == "active" for m in res.json())


def test_soft_delete(client):
    res = client.post("/api/v1/machines", json={"fqdn": "old.example.com", "hostname": "old"})
    mid = res.json()["id"]
    client.delete(f"/api/v1/machines/{mid}")
    res = client.get("/api/v1/machines")
    assert all(m["id"] != mid for m in res.json())


def test_update_machine(client):
    res = client.post("/api/v1/machines", json={"fqdn": "upd.example.com", "hostname": "upd", "ram_gb": 8})
    mid = res.json()["id"]
    res = client.put(f"/api/v1/machines/{mid}", json={"ram_gb": 32})
    assert res.status_code == 200
    assert res.json()["ram_gb"] == 32
