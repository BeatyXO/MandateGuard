# MandateGuard

**Semantic capability firewall for autonomous agents on GenLayer.**

Contract-only repository; no frontend or product application. Local verification: Direct Mode 19/19 passing, Preflight 12/12 passing, GenVM AST lint PASS. StudioNet deployment evidence is not claimed until authenticated live deployment is completed.

MandateGuard is a standalone, reusable Intelligent Contract primitive. A principal creates an immutable natural-language mandate for an agent, the agent proposes an exact action, and GenLayer validators independently judge whether that action is inside the granted authority.

There is **no frontend** in this repository. The intended integration surface is other contracts and agent infrastructure.

## Why this exists

Traditional smart contracts are excellent at deterministic constraints such as:

- spend <= 500
- target == allowlisted_address
- deadline < timestamp

They cannot reliably enforce semantic constraints such as:

> "Book travel for approved conferences, but never buy first-class tickets and escalate any booking involving a non-refundable fare."

MandateGuard makes that boundary reusable on-chain.

## Core flow

1. A principal calls `create_mandate(...)`.
2. The mandate is immutable and bound to:
   - principal
   - agent
   - optional downstream consumer
   - semantic scope
   - hard constraints
   - escalation policy
   - expiry
3. The agent calls `propose_action(...)`.
4. MandateGuard computes an exact SHA-256 fingerprint from canonical JSON: `["MANDATEGUARD_ACTION_V1", mandate_id, agent, action_nonce, target, action_description, action_payload]`.
5. `resolve_action(action_id)` runs GenLayer non-deterministic consensus.
6. Validators independently classify the action as:
   - `AUTHORIZED`
   - `OUT_OF_SCOPE`
   - `REQUIRES_ESCALATION`
7. Downstream contracts can query `is_authorized(action_id)`, `can_execute(mandate_id, action_hash)`, or the consumer-bound `can_execute_for(mandate_id, action_hash, expected_consumer)`.
8. An optional registered consumer can call `consume_authorization(action_id)` to make an approval one-shot.

## Consensus design

MandateGuard deliberately does **not** compare model prose.

Every validator independently evaluates the same mandate and the same proposed action. Consensus is over five stable semantic fields:

- `verdict`
- `scope_fit`
- `hard_constraint_violation`
- `escalation_required`
- `risk_class`

Reasoning, matched-rule prose, and violated-rule prose are stored for auditability but are not consensus-critical.

The contract also applies deterministic fail-closed normalization after the model response:

- a hard-constraint violation always becomes `OUT_OF_SCOPE`
- `scope_fit == OUTSIDE` always becomes `OUT_OF_SCOPE`
- ambiguity or an escalation trigger becomes `REQUIRES_ESCALATION`
- an action cannot remain `AUTHORIZED` unless its scope fit is `INSIDE`

This keeps the semantic judgment non-deterministic while making the state consequence deterministic and bounded.

See [`docs/CONSENSUS.md`](docs/CONSENSUS.md).

## State model

### Mandate

A mandate stores:

- principal address
- agent address
- optional consumer address
- scope
- hard constraints
- escalation policy
- creation and expiry time
- immutable mandate hash
- active/revoked status

Mandates are intentionally immutable. To change authority, revoke the old mandate and create a new one.

### Action

An action stores:

- bound mandate ID and mandate hash
- proposing agent
- target
- human-readable action description
- optional structured payload
- exact action hash
- status
- decision source
- timestamps
- one-shot consumption state

### Decision

A decision stores the validator-agreed fields plus non-consensus audit prose and any principal escalation override.

## Public API

### Writes

```text
create_mandate(agent, consumer, scope, hard_constraints, escalation_policy, ttl_seconds) -> mandate_id
revoke_mandate(mandate_id, reason)
propose_action(mandate_id, action_nonce, target, action_description, action_payload) -> action_id
resolve_action(action_id)
resolve_escalation(action_id, approve, note)
cancel_action(action_id, note)
consume_authorization(action_id)
```

### Views

```text
can_execute(mandate_id, action_hash) -> bool
can_execute_for(mandate_id, action_hash, expected_consumer) -> bool
is_authorized(action_id) -> bool
compute_action_hash(mandate_id, agent, action_nonce, target, action_description, action_payload) -> str
mandate_of(mandate_id) -> JSON
action_of(action_id) -> JSON
decision_of(action_id) -> JSON
stats() -> JSON
```

## Example mandate

```text
Scope:
The agent may arrange travel and accommodation for conferences explicitly approved by the DAO.

Hard constraints:
Never buy first-class air travel.
Never create a booking whose total quoted cost exceeds the treasury's separately enforced spend cap.
Never send funds to a personal wallet.
Never purchase unrelated goods or services.

Escalation policy:
Require principal review for non-refundable bookings, unclear conference approval, or material itinerary changes.
```

An action like:

```text
Target: Airline booking service
Description: Purchase an economy return ticket to the approved conference.
Payload: {"fare_class":"economy","refundability":"refundable","conference":"DevCon"}
```

can be semantically evaluated against that mandate without turning the contract into a generic "AI decides X" wrapper: the output directly gates a reusable authorization state.

## Consumer integration

See [`examples/treasury_agent_consumer.py`](examples/treasury_agent_consumer.py).

A downstream contract should bind execution to the exact `action_id` / `action_hash` and enforce its own deterministic execution rules as well. MandateGuard is a semantic authorization primitive, not a replacement for ordinary access control, spend limits, signatures, or replay protection in the consumer.

## Security properties

- exact mandate binding
- exact action fingerprinting
- immutable mandate semantics
- principal-only revocation
- agent-only proposal creation
- fail-closed consensus normalization
- explicit escalation path
- optional registered-consumer one-shot consumption
- no authorization after mandate expiry or revocation
- prompt-injection language treated as untrusted data

See [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md).

## Repository layout

```text
contracts/
  mandate_guard.py
examples/
  treasury_agent_consumer.py
tests/
  direct/
    conftest.py
    test_mandate_guard.py
docs/
  CONSENSUS.md
  THREAT_MODEL.md
  DEPLOYMENT.md
gltest.config.yaml
requirements-dev.txt
pyproject.toml
LICENSE
```

## Development

Python 3.12+ is recommended.

```bash
python -m pip install -r requirements-dev.txt
genvm-lint check contracts/mandate_guard.py
pytest tests/direct -v
```

The direct tests use GenLayer's test runner mocks so leader and validator LLM calls can be exercised without a live network.

## Deploy

Use GenLayer Studio or the CLI. Full steps are in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

```bash
genlayer deploy --contract contracts/mandate_guard.py
```

For StudioNet testing with `gltest`:

```bash
gltest --network studionet tests/integration/ -v -s
```

## Non-goals

MandateGuard does not:

- execute arbitrary agent tools itself
- custody user funds
- replace deterministic permissions that can be expressed in code
- prove that an agent's description of an off-chain action is truthful
- automatically fetch private data
- silently broaden a mandate

If an authorization decision depends on external evidence, the consumer should supply verifiable context or compose MandateGuard with a separate evidence primitive.

## Submission fit

MandateGuard is intended for the **standalone Intelligent Contracts** category:

- reusable contract primitive
- real GenLayer semantic consensus
- bounded decision space
- clear persistent state transitions
- explicit equivalence checks
- deterministic post-consensus normalization
- integration example
- direct tests
- no frontend/product flow

## License

MIT
