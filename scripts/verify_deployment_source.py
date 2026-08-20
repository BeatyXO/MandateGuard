"""Verify current source against recorded deployment evidence."""
import hashlib
import json
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
p = root / "contracts/mandate_guard.py"
evidence = root / "DEPLOYMENT.json"
current = hashlib.sha256(p.read_bytes()).hexdigest()
if not evidence.exists():
    print("SOURCE PARITY: BLOCKED (DEPLOYMENT.json absent)")
    sys.exit(2)
recorded = json.loads(evidence.read_text())["source_sha256"]
if not recorded:
    print("SOURCE PARITY: BLOCKED (deployment source hash is null)")
    sys.exit(2)
print(f"current={current}")
print(f"recorded={recorded}")
if current != recorded:
    print("SOURCE PARITY: FAIL")
    sys.exit(1)
print("SOURCE PARITY: PASS")
