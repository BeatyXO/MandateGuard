"""Print the reproducible SHA-256 of the deployable contract source."""
import hashlib
from pathlib import Path
p = Path(__file__).resolve().parents[1] / "contracts/mandate_guard.py"
print(hashlib.sha256(p.read_bytes()).hexdigest())
