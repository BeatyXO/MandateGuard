"""Zero-dependency repository invariant checks."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
checks = {
    "contract exists": (ROOT / "contracts/mandate_guard.py").is_file(),
    "single contract candidate": len(list((ROOT / "contracts").glob("*.py"))) == 1,
    "dependency header": '"Depends"' in (ROOT / "contracts/mandate_guard.py").read_text(),
    "collision-safe domains": all(x in (ROOT / "contracts/mandate_guard.py").read_text() for x in ("MANDATEGUARD_ACTION_V1", "MANDATEGUARD_MANDATE_V1")),
    "nonce API": "action_nonce" in (ROOT / "contracts/mandate_guard.py").read_text(),
    "consumer-bound API": "can_execute_for" in (ROOT / "contracts/mandate_guard.py").read_text(),
    "no frontend artifacts": not any((ROOT / n).exists() for n in ("package.json", "next.config.js", "src/app")),
    "source compiles": True,
    "direct tests exist": any((ROOT / "tests/direct").glob("test_*.py")),
    "integration tests exist": any((ROOT / "tests/integration").glob("test_*.py")),
    "docs exist": all((ROOT / n).is_file() for n in ("README.md", "docs/CONSENSUS.md", "docs/THREAT_MODEL.md")),
    "consumer example exists": (ROOT / "examples/treasury_agent_consumer.py").is_file(),
}
try:
    ast.parse((ROOT / "contracts/mandate_guard.py").read_text())
except SyntaxError:
    checks["source compiles"] = False
passed = sum(checks.values())
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + "  " + name)
print(f"Preflight: {passed}/{len(checks)} PASS")
raise SystemExit(0 if passed == len(checks) else 1)
