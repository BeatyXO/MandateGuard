# StudioNet deployment evidence

| Item | Verified value |
|---|---|
| Network / chain ID | StudioNet / 61999 |
| Contract | `0x7036E2B16d0CA5ae68B154752f628d9bf804fC31` |
| Explorer | https://explorer-studio.genlayer.com/address/0x7036E2B16d0CA5ae68B154752f628d9bf804fC31 |
| Deployment status | ACCEPTED / MAJORITY_AGREE |
| Source commit | `f7a6c2589e8ac087c7e4f337ddc5c147a65f2114` |
| Contract SHA-256 | `9a462af50d52883634fd71479d11130d262491aca948c7bb5b8d61ae1ac0a76e` |
| Direct Mode | 19 passed |
| StudioNet integration | 1 full-cycle test passed after a transient hosted-RPC 502 retry |

The hosted Studio runner did not retain the deployment receipt transaction hash in its first successful run, so `DEPLOYMENT.json` records it as `null` rather than inventing one. All post-deployment proof transaction hashes are real and recorded below.

| Scenario | Transaction | Result |
|---|---|---|
| AUTHORIZED semantic resolution | `0xb09dab5ca89ee62d40957b8206afacf78620d4f5e4ae3517c78956b34595ae39` | AUTHORIZED |
| One-shot consumption | `0x1c1256804aec5c7d80444e4afb21f72af9017546c51fed1928f2e3e918f6634e` | consumed; authorization views became false |
| OUT_OF_SCOPE semantic resolution | `0xa4db30c6e4aa6702471d03d6d841ed3e000d9cda2e3a465d64eb02e39e9fa318` | OUT_OF_SCOPE |
| REQUIRES_ESCALATION resolution | `0xbfb1e7512ee33a6d48289d8e0fc3d7348785ef2e0b2e4d58415237441b29a51e` | REQUIRES_ESCALATION |
| Principal approval | `0xf85e45e695ecc347abd0c68b450169b9791529add772ddb2de38e4c907c39ef6` | AUTHORIZED via principal override |
| Cancellation | `0x0f33dfc72f5c08d2559c5cae2f82b90612ea1bfb06a21699242f75e35fb0df99` | CANCELLED |
| Revocation | `0x50d02c4d96bef54337a725c59e4f352cd8707c4c7787a16fcf24e54a19f4c7d5` | prior authorization invalidated |

Run `python scripts/verify_deployment_source.py` to check that the current contract bytes remain identical to the recorded deployed source hash.
