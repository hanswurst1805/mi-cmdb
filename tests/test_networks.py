def test_create_network(client):
    res = client.post("/api/v1/networks", json={
        "name": "Production",
        "cidr": "10.0.0.0/24",
        "gateway": "10.0.0.1",
        "location": "Berlin",
    })
    assert res.status_code == 201
    assert res.json()["cidr"] == "10.0.0.0/24"


def test_invalid_cidr(client):
    res = client.post("/api/v1/networks", json={"name": "Bad", "cidr": "not-a-cidr"})
    assert res.status_code == 422


def test_duplicate_cidr(client):
    payload = {"name": "Net", "cidr": "192.168.1.0/24"}
    client.post("/api/v1/networks", json=payload)
    res = client.post("/api/v1/networks", json={"name": "Net2", "cidr": "192.168.1.0/24"})
    assert res.status_code == 409


def test_free_ips(client):
    net_res = client.post("/api/v1/networks", json={"name": "Small", "cidr": "10.10.10.0/30"})
    nid = net_res.json()["id"]
    res = client.get(f"/api/v1/networks/{nid}/free")
    assert res.status_code == 200
    assert len(res.json()["free_ips"]) == 2  # /30 hat 2 Hosts
