# Deployment and Verification

## Prerequisites

- Python 3.12+
- GenLayer CLI
- GenLayer test suite
- GenVM linter
- a funded account for the target network

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

## 1. Lint

```bash
genvm-lint check contracts/mandate_guard.py
```

Do not deploy if SDK validation reports an error.

## 2. Direct tests

```bash
pytest tests/direct -v
```

The direct suite covers mandate binding, agent-only proposals, duplicate prevention, semantic authorization, hard-constraint denial, ambiguity escalation, principal override, revocation, expiry, action-hash binding, one-shot consumption, and malformed model output.

## 3. Local deployment

```bash
genlayer network set localnet
genlayer deploy --contract contracts/mandate_guard.py
```

Record the contract address and deployment transaction.

## 4. StudioNet deployment

```bash
genlayer network set studionet
genlayer deploy --contract contracts/mandate_guard.py
```

Then exercise one action for each outcome:

```text
AUTHORIZED
OUT_OF_SCOPE
REQUIRES_ESCALATION
```

Suggested test mandate:

```text
Scope:
Arrange travel for conferences explicitly approved by the DAO.

Hard constraints:
Never purchase first-class travel.
Never send funds to a personal wallet.

Escalation policy:
Escalate non-refundable bookings or unclear conference approval.
```

Suggested actions:

1. Refundable economy ticket to an approved conference -> expected `AUTHORIZED`.
2. First-class ticket -> expected `OUT_OF_SCOPE`.
3. Non-refundable economy ticket -> expected `REQUIRES_ESCALATION`.

## 5. Submission evidence

Record:

```text
network
contract address
deployment transaction
source commit SHA
authorized-action transaction
out-of-scope transaction
escalation transaction
```

## 6. Verify source parity

The dependency header is intentionally pinned:

```text
py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6
```

Do not edit the source after deployment and claim parity with the older deployment. If source changes, redeploy and update the recorded commit/address pair.
