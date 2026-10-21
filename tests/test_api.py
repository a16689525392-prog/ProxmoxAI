import os
import pytest
from fastapi.testclient import TestClient
from proxmoxai.agent import rule_plan, PlanningError
from proxmoxai.config import Settings
from proxmoxai.main import app, Runtime

@pytest.fixture
def client():
    settings = Settings(app_api_key="test-unique-secret-key",mock_mode=True,allowed_vmids="101,102,103")
    app.state.runtime = Runtime(settings)
    with TestClient(app) as c:
        yield c
    del app.state.runtime

def headers():
    return {"X-API-Key":"test-unique-secret-key"}

def test_health(client):
    assert client.get("/healthz").json()["ok"] is True

def test_auth(client):
    assert client.get("/api/vms").status_code == 401

def test_inventory(client):
    ids = {v["vmid"] for v in client.get("/api/vms",headers=headers()).json()}
    assert ids == {101,102,103}

def test_agent_plan(client):
    r=client.post("/api/agent/plan",headers=headers(),json={"text":"启动虚拟机 102"})
    assert r.status_code==200 and r.json()["plan"]["intent"]=="start"

def test_negative_refused():
    with pytest.raises(PlanningError):
        rule_plan("不要启动虚拟机 102")

def test_cross_vm_rejected(client):
    r=client.post("/api/vms/pve-demo/999/preview",headers=headers(),json={"action":"start"})
    assert r.status_code==403

def test_confirm_once(client):
    r=client.post("/api/vms/pve-demo/102/preview",headers=headers(),json={"action":"start"})
    assert r.status_code==200
    approval=r.json()["approval_id"]
    r=client.post("/api/actions/execute",headers=headers(),json={"approval_id":approval})
    assert r.status_code==200
    assert r.json()["accepted"]
    r=client.post("/api/actions/execute",headers=headers(),json={"approval_id":approval})
    assert r.status_code==409

def test_snapshot_requires_name(client):
    assert client.post("/api/vms/pve-demo/101/preview",headers=headers(),json={"action":"snapshot"}).status_code==422

def test_shutdown(client):
    r=client.post("/api/vms/pve-demo/101/preview",headers=headers(),json={"action":"shutdown"})
    assert r.status_code==200
    r=client.post("/api/actions/execute",headers=headers(),json={"approval_id":r.json()["approval_id"]})
    assert r.status_code==200
