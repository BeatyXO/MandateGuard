# Deployment evidence

Only verified results belong here. This checkout has no authenticated StudioNet deployment; `DEPLOYMENT.json` therefore contains null live identifiers and source parity is blocked until deployment evidence is recorded.

## Local verification

Run `python scripts/preflight.py`, `pytest tests/direct/ -v`, and `genvm-lint check contracts/mandate_guard.py`. Record exact outputs and exit codes; do not claim lint PASS without exit code 0.

## StudioNet evidence

Network: StudioNet
Chain ID: 61999
Contract, deployment transaction, finalization state, source commit, and source hash: recorded in `DEPLOYMENT.json` after authenticated deployment. Explorer format: `https://explorer-studio.genlayer.com/address/<CONTRACT_ADDRESS>`.

The live proof table must contain real transaction hashes for AUTHORIZED, OUT_OF_SCOPE, REQUIRES_ESCALATION, principal resolution, consumption/replay, cancellation, and revocation. No placeholder hashes are acceptable.

## Source parity

After deployment, populate `DEPLOYMENT.json` and run `python scripts/verify_deployment_source.py`. It compares the current contract bytes to the deployed SHA-256 and exits non-zero on mismatch.
