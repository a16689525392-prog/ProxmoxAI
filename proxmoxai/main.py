"""FastAPI control plane: planning is separate from action execution."""
import asyncio
import re
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .config import get_settings, Settings
from .models import AgentRequest, PreviewRequest, ExecuteRequest, Action
from .agent import plan_command, PlanningError
from .providers import MockPVE, RealPVE, PVEError

WEB_DIR = Path(__file__).resolve().parents[1] / "web"
app = FastAPI(title="ProxmoxAI", version="0.1.0", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

@dataclass
class Approval:
    node: str
    vmid: int
    action: Action
    snapname: str | None
    expires: float

class Runtime:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = MockPVE(settings.vmids) if settings.mock_mode else RealPVE(settings)
        self.pending: dict[str,Approval] = {}
        self.lock = asyncio.Lock()

def get_runtime():
    if not hasattr(app.state,"runtime"):
        app.state.runtime = Runtime(get_settings())
    return app.state.runtime

def auth(x_api_key: str | None = Header(default=None), rt: Runtime = Depends(get_runtime)):
    if x_api_key is None or not secrets.compare_digest(x_api_key,rt.settings.app_api_key):
        raise HTTPException(401,"Invalid API key")

async def find_vm(rt: Runtime,node:str,vmid:int):
    if vmid not in rt.settings.vmids:
        raise HTTPException(403,"VM outside ALLOWED_VMIDS")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}",node):
        raise HTTPException(400,"Invalid node")
    matching = [v for v in await rt.provider.list_vms() if v.node==node and v.vmid==vmid]
    if len(matching)!=1:
        raise HTTPException(404,"VM not found")
    return matching[0]

@app.get("/")
async def index():
    return FileResponse(WEB_DIR/"index.html")

@app.get("/healthz")
async def healthz():
    return {"ok":True}

@app.get("/api/meta", dependencies=[Depends(auth)])
async def meta(rt:Runtime=Depends(get_runtime)):
    return {"version":"0.1.0","mode":"demo" if rt.settings.mock_mode else "live","vmids":sorted(rt.settings.vmids)}

@app.get("/api/vms", dependencies=[Depends(auth)])
async def inventory(rt:Runtime=Depends(get_runtime)):
    try:
        return await rt.provider.list_vms()
    except PVEError as exc:
        raise HTTPException(502,str(exc)) from None

@app.post("/api/agent/plan", dependencies=[Depends(auth)])
async def plan(req: AgentRequest,rt:Runtime=Depends(get_runtime)):
    try:
        result = await plan_command(req.text,rt.settings)
        if result.vmid is None:
            return {"plan":result,"vm":None}
        if result.vmid not in rt.settings.vmids:
            raise HTTPException(403,"VM outside ALLOWED_VMIDS")
        candidates = [v for v in await rt.provider.list_vms() if v.vmid==result.vmid]
        if len(candidates)!=1:
            raise HTTPException(404,"VM missing or ambiguous")
        return {"plan":result,"vm":candidates[0]}
    except PlanningError as exc:
        raise HTTPException(422,str(exc)) from None
    except PVEError as exc:
        raise HTTPException(502,str(exc)) from None

@app.post("/api/vms/{node}/{vmid}/preview",dependencies=[Depends(auth)])
async def preview(node:str,vmid:int,req:PreviewRequest,rt:Runtime=Depends(get_runtime)):
    try:
        vm = await find_vm(rt,node,vmid)
        state = (await rt.provider.status(vm)).get("status","unknown")
    except PVEError as exc:
        raise HTTPException(502,str(exc)) from None
    if req.action == Action.snapshot and not req.snapname:
        raise HTTPException(422,"Snapshot name required")
    if req.action != Action.snapshot and req.snapname is not None:
        raise HTTPException(422,"Snapshot name is only for snapshots")
    if req.action==Action.start and state!="stopped":
        raise HTTPException(409,"VM is not stopped")
    if req.action==Action.shutdown and state!="running":
        raise HTTPException(409,"VM is not running")
    identifier = secrets.token_urlsafe(32)
    async with rt.lock:
        now = time.monotonic()
        rt.pending = {key:value for key,value in rt.pending.items() if value.expires>now}
        rt.pending[identifier] = Approval(node,vmid,req.action,req.snapname,now+90)
    return {"approval_id":identifier,"expires_in_seconds":90,"action":req.action,
            "target":{"vmid":vmid,"node":node,"name":vm.name,"status":state},"snapname":req.snapname}

@app.post("/api/actions/execute",dependencies=[Depends(auth)])
async def execute(req:ExecuteRequest,rt:Runtime=Depends(get_runtime)):
    async with rt.lock:
        approval = rt.pending.pop(req.approval_id,None)
    if approval is None or approval.expires<=time.monotonic():
        raise HTTPException(409,"Approval missing, expired or reused")
    try:
        vm = await find_vm(rt,approval.node,approval.vmid)
        state = (await rt.provider.status(vm)).get("status","unknown")
        if approval.action==Action.start and state!="stopped":
            raise HTTPException(409,"VM state changed")
        if approval.action==Action.shutdown and state!="running":
            raise HTTPException(409,"VM state changed")
        task = await rt.provider.act(vm,approval.action,approval.snapname)
    except PVEError as exc:
        raise HTTPException(502,str(exc)) from None
    return {"accepted":True,"mode":"demo" if rt.settings.mock_mode else "live",
            "node":vm.node,"vmid":vm.vmid,"action":approval.action,"task_upid":task,
            "message":"Demo action completed" if rt.settings.mock_mode else "PVE task submitted; completion pending"}
