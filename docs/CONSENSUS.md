# Consensus and Equivalence Design

MandateGuard keeps the consensus question intentionally narrow:

> For one immutable mandate and one exact proposed action, is the action clearly authorized, clearly outside authority, or does it require principal escalation?

Mandate identity is also domain-separated and collision-safe: the mandate hash is SHA-256 of canonical JSON beginning with `MANDATEGUARD_MANDATE_V1` and containing the mandate ID, principal, agent, consumer, scope, hard constraints, escalation policy, creation time, and expiry. Action identity uses `MANDATEGUARD_ACTION_V1` and canonical JSON containing mandate ID, lowercase agent, action nonce, target, description, and payload.

## Structured decision

The leader returns:

```json
{
  "verdict": "AUTHORIZED | OUT_OF_SCOPE | REQUIRES_ESCALATION",
  "scope_fit": "INSIDE | OUTSIDE | AMBIGUOUS",
  "hard_constraint_violation": false,
  "escalation_required": false,
  "risk_class": "LOW | MEDIUM | HIGH | CRITICAL",
  "reason": "...",
  "matched_rules": "...",
  "violated_rules": "..."
}
```

Each validator independently reruns the same classification from the original mandate and action. It does not merely check that the leader returned valid JSON.

## Equivalence rule

Consensus requires equality on five decision-critical fields:

```text
verdict
scope_fit
hard_constraint_violation
escalation_required
risk_class
```

`reason`, `matched_rules`, and `violated_rules` are excluded from equivalence because validators can explain the same judgment differently.

Required booleans must be JSON booleans and enums must be supported strings. Malformed or incorrectly typed output fails closed to `REQUIRES_ESCALATION`, `AMBIGUOUS`, `HIGH`. Principal override metadata is deterministic contract state; LLM values are ignored and only `resolve_escalation` can set it.

## Deterministic fail-closed normalization

Before comparison and storage:

1. Unknown verdict -> `REQUIRES_ESCALATION`.
2. Unknown scope -> `AMBIGUOUS`.
3. Unknown risk -> `HIGH`.
4. A hard-constraint violation forces `OUT_OF_SCOPE`.
5. `scope_fit == OUTSIDE` forces `OUT_OF_SCOPE`.
6. `escalation_required == true` forces `REQUIRES_ESCALATION`, unless a hard violation already denies the action.
7. `scope_fit == AMBIGUOUS` forces `REQUIRES_ESCALATION`.
8. `AUTHORIZED` is accepted only with `scope_fit == INSIDE`.

This prevents internally inconsistent model output from becoming authorization state.

## Why risk class participates in consensus

Risk does not itself grant permission, but it is part of the stored authorization dossier and may be consumed by downstream contracts. If an importer later applies a deterministic rule such as "only LOW/MEDIUM actions auto-execute", the risk classification must be validator-agreed.

## Escalation

Consensus can return `REQUIRES_ESCALATION`. The principal may then approve or deny that exact action. The override cannot rewrite the mandate, is recorded in the decision dossier, and is unavailable after revocation or expiry.

## Counter semantics

`authorized_count`, `denied_count`, and `escalation_count` are transition/event counters, not mutually exclusive current action totals. Opening an escalation increments `escalation_count`; principal approval or denial later increments the corresponding authorized or denied counter. `consumed_count` counts irreversible consumption events.
