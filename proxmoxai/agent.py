"""Plain-language input never has authority to execute operations."""
import json
import re
import httpx
from .models import Plan
from .config import Settings

class PlanningError(ValueError): pass

def rule_plan(text: str) -> Plan:
    text = text.strip()
    lower = text.lower()
    if any(t in lower for t in ("不要","别","禁止","don't","do not","not start")):
        raise PlanningError("Negated instructions are refused")
    ids = re.findall(r"(?<!\d)\d{3,9}(?!\d)", lower)
    if len(set(ids)) > 1:
        raise PlanningError("One VM ID per request")
    vmid = int(ids[0]) if ids else None
    matches = []
    for intent, words in [
        ("snapshot", ("快照","snapshot")),
        ("shutdown", ("关机","关闭虚拟机","shutdown","shut down","power off")),
        ("start", ("开机","启动","start vm","power on","boot vm")),
        ("status", ("状态","status","运行情况")),
        ("list", ("列表","列出","所有虚拟机","list vm","show vms"))
    ]:
        if any(w in lower for w in words):
            matches.append(intent)
    if len(matches) != 1:
        raise PlanningError("Specify exactly one operation")
    intent = matches[0]
    if intent != "list" and vmid is None:
        raise PlanningError("Provide an explicit VM ID")
    if intent == "list" and vmid is not None:
        raise PlanningError("List action cannot target one VM")
    name = None
    if intent == "snapshot":
        m = re.search(r"(?:名为|名称(?:为)?|named|name)\s*[:：]?\s*([A-Za-z][A-Za-z0-9_-]{0,39})", text, re.I)
        name = m.group(1) if m else None
    return Plan(intent=intent, vmid=vmid, snapname=name, explanation="Deterministic parser", source="rules")

async def plan_command(text: str, settings: Settings) -> Plan:
    if re.search(r"不要|别|禁止|don't|do not", text, re.I) or len(set(re.findall(r"(?<!\d)\d{3,9}(?!\d)", text))) > 1:
        raise PlanningError("Ambiguous or negated instruction")
    if not settings.openai_api_key:
        return rule_plan(text)
    system = ("Parse Proxmox commands to JSON fields intent,vmid,snapname,explanation. "
              "intent must be list,status,start,shutdown,snapshot. Refuse ambiguous requests by "
              "setting explanation to AMBIGUOUS. No tools and no arbitrary commands.")
    payload = {"model": settings.openai_model, "temperature": 0,
               "messages": [{"role":"system","content":system},{"role":"user","content":text}]}
    try:
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            r = await client.post(settings.openai_base_url.rstrip("/") + "/chat/completions",
                headers={"Authorization":"Bearer " + settings.openai_api_key}, json=payload)
            r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I)
        plan = Plan.model_validate(json.loads(raw))
        ids = {int(v) for v in re.findall(r"(?<!\d)\d{3,9}(?!\d)", text)}
        if plan.explanation == "AMBIGUOUS" or (plan.intent != "list" and plan.vmid not in ids):
            raise PlanningError("VM target must be explicit and unambiguous")
        if plan.intent == "list" and plan.vmid is not None:
            raise PlanningError("Invalid list intent")
        plan.source = "llm"
        return plan
    except PlanningError:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise PlanningError("AI parser unavailable; disable OPENAI_API_KEY to use offline rules") from None
