# Threat Model

MandateGuard is a semantic authorization primitive. It should be composed with normal deterministic controls.

## Prompt injection inside mandate/action text

The validator prompt treats mandate and action content as untrusted data and explicitly ignores embedded role changes, prompt requests, or decision instructions.

## Broad scope overriding a specific prohibition

Hard constraints have precedence. Deterministic normalization forces any reported hard-constraint violation to `OUT_OF_SCOPE`.

## Ambiguous action accidentally authorized

Ambiguity fails closed to `REQUIRES_ESCALATION`. Missing permissions are not inferred.

## Action changed after authorization

Every proposal receives a SHA-256 fingerprint over:

```text
mandate_id
agent
target
action_description
action_payload
```

Consumers should bind execution to that exact action ID/hash.

## Mandate changed after authorization

Mandates are immutable. Every action stores the mandate hash present when proposed. Changing authority requires revocation and a new mandate.

## Revoked/expired mandate remains usable

`is_authorized` and `can_execute` re-check current mandate state and expiry every time.

## Authorization replay

A registered consumer can call `consume_authorization` once. Consumers should additionally maintain their own executed-action set when execution and consumption are not atomic across contracts.

## Malicious proposer

Only the exact agent address named in the mandate can create proposals.

## Unauthorized escalation override

Only the mandate principal can resolve `REQUIRES_ESCALATION`.

## Well-formed but wrong leader output

Validators independently rerun the classification and compare decision-critical fields. Shape validation alone is not treated as semantic consensus.

## False external-world claims

MandateGuard judges the action description it receives. It does not prove that an off-chain claim is true. If authorization depends on external facts, compose with an evidence/source primitive or a purpose-built importer.

## Deterministic rules delegated to AI

Do not use MandateGuard for constraints that ordinary code can enforce exactly. Spend ceilings, allowlists, signatures, timelocks, exact token amounts, and address equality belong in deterministic consumer logic.
