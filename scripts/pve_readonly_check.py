"""Read-only opt-in verification against a real Proxmox VE lab.

Requires .env with MOCK_MODE=false and a dedicated PVE API token.
Never mutates VMs or prints credentials.
"""
import asyncio
import json
import sys
from datetime import datetime, timezone

from proxmoxai.config import get_settings
from proxmoxai.providers import PVEError, RealPVE

async def check() -> int:
    config = get_settings()
    if config.mock_mode:
        print("REFUSED: Set MOCK_MODE=false for real PVE validation.", file=sys.stderr)
        return 2
    if not config.pve_verify_ssl:
        print("REFUSED: PVE_VERIFY_SSL must be true.", file=sys.stderr)
        return 2
    provider = RealPVE(config)
    try:
        vms = await provider.list_vms()
        if not vms:
            print("FAIL: No allowlisted QEMU VM is visible.", file=sys.stderr)
            return 1
        states = []
        for vm in vms:
            detail = await provider.status(vm)
            if not isinstance(detail, dict) or not detail.get("status"):
                raise PVEError("PVE VM state missing")
            states.append({"vmid":vm.vmid, "status":detail["status"]})
    except PVEError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "test": "read-only PVE API integration",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "result": "PASS",
        "allowed_vm_count": len(vms),
        "vms": states,
        "mutating_actions_tested": False
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(check()))
    except ValueError as exc:
        print(f"CONFIG ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
