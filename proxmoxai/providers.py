"""Real and mocked Proxmox REST providers."""
from collections.abc import Iterable
import httpx
from .config import Settings
from .models import VM, Action

class PVEError(Exception): pass

class RealPVE:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def request(self, method: str, path: str, data: dict | None = None):
        s = self.settings
        headers = {"Authorization": f"PVEAPIToken={s.pve_token_id}={s.pve_token_secret}"}
        try:
            async with httpx.AsyncClient(timeout=15, verify=s.pve_verify_ssl, trust_env=False) as client:
                res = await client.request(method, s.pve_api_url.rstrip("/") + "/api2/json" + path, headers=headers, data=data)
                res.raise_for_status()
                payload = res.json()
            if not isinstance(payload, dict) or "data" not in payload:
                raise PVEError("Malformed PVE response")
            return payload["data"]
        except httpx.HTTPStatusError as exc:
            raise PVEError(f"PVE HTTP {exc.response.status_code}; verify token permissions") from None
        except (httpx.RequestError, ValueError):
            raise PVEError("Could not securely reach Proxmox VE") from None

    async def list_vms(self):
        data = await self.request("GET", "/cluster/resources?type=vm")
        if not isinstance(data, list):
            raise PVEError("Invalid VM list")
        return [VM(vmid=int(v["vmid"]), node=v["node"], name=v.get("name",f'VM-{v["vmid"]}'),
                   status=v.get("status","unknown"), cpu=v.get("cpu") or 0,
                   mem=v.get("mem") or 0,maxmem=v.get("maxmem") or 0)
                for v in data if v.get("type") == "qemu" and int(v.get("vmid",0)) in self.settings.vmids]

    async def status(self, vm: VM):
        return await self.request("GET", f"/nodes/{vm.node}/qemu/{vm.vmid}/status/current")

    async def act(self, vm: VM, action: Action, snapname: str | None = None):
        path = f"/nodes/{vm.node}/qemu/{vm.vmid}"
        if action == Action.snapshot:
            return await self.request("POST", path + "/snapshot", {"snapname":snapname,"description":"Approved operation via ProxmoxAI"})
        return await self.request("POST", path + "/status/" + action.value)

class MockPVE:
    def __init__(self, allowed: Iterable[int]):
        self.vms = {i:VM(vmid=i,node="pve-demo",name=f"demo-{i}",status="running" if pos%2==0 else "stopped",
                      cpu=0.05,maxmem=4*1024**3) for pos,i in enumerate(sorted(allowed))}
        self.snapshots = {i:[] for i in allowed}

    async def list_vms(self):
        return [v.model_copy(deep=True) for v in self.vms.values()]

    async def status(self, vm: VM):
        v = self.vms[vm.vmid]
        return {"status":v.status,"node":v.node,"vmid":v.vmid}

    async def act(self, vm: VM, action: Action, snapname: str | None = None):
        if action == Action.start:
            self.vms[vm.vmid].status = "running"
        elif action == Action.shutdown:
            self.vms[vm.vmid].status = "stopped"
        else:
            self.snapshots[vm.vmid].append(snapname)
        return "MOCK:completed"
