# MandateGuard submission

Category: Standalone Intelligent Contracts. MandateGuard is a contract-only semantic capability firewall: an immutable principal mandate constrains an agent's exact, nonce-identified action, while independent GenLayer validators produce bounded semantic authorization state.

GenLayer is load-bearing because deterministic code cannot reliably interpret semantic boundaries such as “services directly related to approved research.” Validators independently evaluate the same mandate and action; deterministic normalization, equivalence, expiry, replay, revocation, and consumer binding decide what that observation can authorize.

The model cannot transfer funds, alter mandates, forge principal approval, select arbitrary targets, bypass replay, or execute tools. Malformed output fails closed to `REQUIRES_ESCALATION`.

Primary review order: `contracts/mandate_guard.py`, `tests/direct/`, `examples/treasury_agent_consumer.py`, `docs/CONSENSUS.md`, `docs/THREAT_MODEL.md`, `README.md`.

Live deployment identifiers are intentionally recorded in `docs/DEPLOYMENT.md` only after an authenticated StudioNet deployment; no fabricated evidence is included.
