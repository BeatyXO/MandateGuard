import json

import pytest

from conftest import warp_to


CONTRACT = "contracts/mandate_guard.py"
ZERO = "0x0000000000000000000000000000000000000000"
SCOPE = "Arrange travel and accommodation only for conferences explicitly approved by the DAO."
CONSTRAINTS = "Never buy first-class travel. Never send funds to a personal wallet."
ESCALATION = "Escalate non-refundable bookings or unclear conference approval."


def deploy(direct_deploy, direct_vm):
    contract = direct_deploy(CONTRACT)
    direct_vm.check_pickling = True
    return contract


def create(contract, direct_vm, principal, agent, consumer=ZERO, ttl=86400):
    direct_vm.sender = principal
    return contract.create_mandate(agent, consumer, SCOPE, CONSTRAINTS, ESCALATION, ttl)


def propose(contract, direct_vm, agent, description, payload='{"conference":"DevCon"}'):
    direct_vm.sender = agent
    return contract.propose_action(1, "travel-booking-service", description, payload)


def mock_decision(direct_vm, verdict="AUTHORIZED", scope_fit="INSIDE", hard=False, escalate=False, risk="LOW"):
    direct_vm.clear_mocks()
    direct_vm.mock_llm(
        r".*semantic capability firewall.*",
        json.dumps({
            "verdict": verdict,
            "scope_fit": scope_fit,
            "hard_constraint_violation": hard,
            "escalation_required": escalate,
            "risk_class": risk,
            "reason": "bounded test decision",
            "matched_rules": "conference travel",
            "violated_rules": "first-class prohibition" if hard else "none",
        }),
    )


def test_create_mandate_stores_binding(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = deploy(direct_deploy, direct_vm)
    assert create(contract, direct_vm, direct_alice, direct_bob) == 1
    mandate = json.loads(contract.mandate_of(1))
    assert mandate["principal"].lower() == str(direct_alice).lower()
    assert mandate["agent"].lower() == str(direct_bob).lower()
    assert mandate["status"] == "ACTIVE"
    assert len(mandate["mandate_hash"]) == 64


@pytest.mark.parametrize("scope,constraints,ttl", [("", CONSTRAINTS, 86400), (SCOPE, "", 86400), (SCOPE, CONSTRAINTS, 1)])
def test_create_rejects_invalid_inputs(direct_deploy, direct_vm, direct_alice, direct_bob, scope, constraints, ttl):
    contract = deploy(direct_deploy, direct_vm)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("EXPECTED"):
        contract.create_mandate(direct_bob, ZERO, scope, constraints, ESCALATION, ttl)


def test_only_bound_agent_can_propose(direct_deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_deploy, direct_vm)
    create(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("EXPECTED"):
        contract.propose_action(1, "target", "Book economy travel to approved conference.", "{}")


def test_action_hash_binds_exact_action(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = deploy(direct_deploy, direct_vm)
    create(contract, direct_vm, direct_alice, direct_bob)
    action_id = propose(contract, direct_vm, direct_bob, "Book refundable economy travel to approved conference.")
    action = json.loads(contract.action_of(action_id))
    expected = contract.compute_action_hash(1, direct_bob, action["target"], action["action_description"], action["action_payload"])
    assert action["action_hash"] == expected
    assert len(expected) == 64


def test_duplicate_exact_action_rejected(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = deploy(direct_deploy, direct_vm)
    create(contract, direct_vm, direct_alice, direct_bob)
    description = "Book refundable economy travel to approved conference."
    propose(contract, direct_vm, direct_bob, description)
    with direct_vm.expect_revert("EXPECTED"):
        propose(contract, direct_vm, direct_bob, description)


def test_consensus_authorizes_clear_action(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = deploy(direct_deploy, direct_vm)
    create(contract, direct_vm, direct_alice, direct_bob)
    action_id = propose(contract, direct_vm, direct_bob, "Book refundable economy travel to approved conference.")
    mock_decision(direct_vm)
    contract.resolve_action(action_id)
    action = json.loads(contract.action_of(action_id))
    assert action["status"] == "AUTHORIZED"
    assert contract.is_authorized(action_id) is True
    assert contract.can_execute(1, action["action_hash"]) is True


def test_hard_constraint_violation_denied(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = deploy(direct_deploy, direct_vm)
    create(contract, direct_vm, direct_alice, direct_bob)
    action_id = propose(contract, direct_vm, direct_bob, "Purchase a first-class ticket to the approved conference.")
    mock_decision(direct_vm, verdict="AUTHORIZED", scope_fit="INSIDE", hard=True, risk="HIGH")
    contract.resolve_action(action_id)
    assert json.loads(contract.action_of(action_id))["status"] == "OUT_OF_SCOPE"
    assert contract.is_authorized(action_id) is False


def test_ambiguous_scope_escalates(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = deploy(direct_deploy, direct_vm)
    create(contract, direct_vm, direct_alice, direct_bob)
    action_id = propose(contract, direct_vm, direct_bob, "Book travel to a conference whose approval status is unclear.")
    mock_decision(direct_vm, verdict="AUTHORIZED", scope_fit="AMBIGUOUS", risk="MEDIUM")
    contract.resolve_action(action_id)
    assert json.loads(contract.action_of(action_id))["status"] == "REQUIRES_ESCALATION"


def test_principal_can_approve_escalation(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = deploy(direct_deploy, direct_vm)
    create(contract, direct_vm, direct_alice, direct_bob)
    action_id = propose(contract, direct_vm, direct_bob, "Book a non-refundable economy ticket.")
    mock_decision(direct_vm, verdict="REQUIRES_ESCALATION", scope_fit="INSIDE", escalate=True, risk="MEDIUM")
    contract.resolve_action(action_id)
    direct_vm.sender = direct_alice
    contract.resolve_escalation(action_id, True, "Approved after manual review.")
    action = json.loads(contract.action_of(action_id))
    decision = json.loads(contract.decision_of(action_id))
    assert action["status"] == "AUTHORIZED"
    assert action["decision_source"] == "PRINCIPAL"
    assert decision["principal_override"] is True


def test_revocation_invalidates_prior_authorization(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = deploy(direct_deploy, direct_vm)
    create(contract, direct_vm, direct_alice, direct_bob)
    action_id = propose(contract, direct_vm, direct_bob, "Book refundable economy travel to approved conference.")
    mock_decision(direct_vm)
    contract.resolve_action(action_id)
    direct_vm.sender = direct_alice
    contract.revoke_mandate(1, "Agent rotation")
    assert contract.is_authorized(action_id) is False


def test_expiry_invalidates_authorization(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = deploy(direct_deploy, direct_vm)
    warp_to(direct_vm, "2026-08-20T12:00:00Z")
    create(contract, direct_vm, direct_alice, direct_bob, ttl=300)
    action_id = propose(contract, direct_vm, direct_bob, "Book refundable economy travel to approved conference.")
    mock_decision(direct_vm)
    contract.resolve_action(action_id)
    assert contract.is_authorized(action_id) is True
    warp_to(direct_vm, "2026-08-20T12:06:00Z")
    assert contract.is_authorized(action_id) is False


def test_registered_consumer_can_consume_once(direct_deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_deploy, direct_vm)
    create(contract, direct_vm, direct_alice, direct_bob, consumer=direct_charlie)
    action_id = propose(contract, direct_vm, direct_bob, "Book refundable economy travel to approved conference.")
    mock_decision(direct_vm)
    contract.resolve_action(action_id)
    direct_vm.sender = direct_charlie
    contract.consume_authorization(action_id)
    assert contract.is_authorized(action_id) is False
    with direct_vm.expect_revert("EXPECTED"):
        contract.consume_authorization(action_id)


def test_malformed_model_output_fails_closed(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = deploy(direct_deploy, direct_vm)
    create(contract, direct_vm, direct_alice, direct_bob)
    action_id = propose(contract, direct_vm, direct_bob, "Book economy travel.")
    direct_vm.clear_mocks()
    direct_vm.mock_llm(r".*semantic capability firewall.*", "not json")
    contract.resolve_action(action_id)
    decision = json.loads(contract.decision_of(action_id))
    assert json.loads(contract.action_of(action_id))["status"] == "REQUIRES_ESCALATION"
    assert decision["risk_class"] == "HIGH"


def test_resolved_action_cannot_be_replayed(direct_deploy, direct_vm, direct_alice, direct_bob):
    contract = deploy(direct_deploy, direct_vm)
    create(contract, direct_vm, direct_alice, direct_bob)
    action_id = propose(contract, direct_vm, direct_bob, "Book refundable economy travel to approved conference.")
    mock_decision(direct_vm)
    contract.resolve_action(action_id)
    with direct_vm.expect_revert("EXPECTED"):
        contract.resolve_action(action_id)
