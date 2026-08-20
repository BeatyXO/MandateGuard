import json
import os

import pytest
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_STUDIONET_GLTEST_NONDET") != "1",
    reason="opt-in StudioNet integration",
)

ZERO = "0x0000000000000000000000000000000000000000"


def _record(label, receipt):
    print("LIVE_" + label + "=" + json.dumps(receipt, default=str, sort_keys=True))
    assert tx_execution_succeeded(receipt)


def test_full_surface_on_studionet(default_account):
    factory = get_contract_factory("MandateGuard")
    contract = factory.deploy(account=default_account).connect(default_account)
    agent = str(default_account.address)
    print("LIVE_CONTRACT_ADDRESS=" + str(contract.address))

    created = contract.create_mandate(
        args=[
            agent,
            str(default_account.address),
            "Arrange travel only for conferences explicitly approved by the DAO.",
            "Never buy first-class travel. Never send funds to a personal wallet.",
            "Escalate non-refundable bookings or unclear conference approval.",
            86400,
        ]
    ).transact()
    _record("MANDATE_CREATED", created)

    opened = contract.propose_action(
        args=[
            1,
            "authorized-1",
            "travel-booking-service",
            "Book a refundable economy ticket to an approved conference.",
            '{"fare_class":"economy","refundability":"refundable"}',
        ]
    ).transact()
    _record("AUTHORIZED_PROPOSED", opened)

    resolved = contract.resolve_action(args=[1]).transact(wait_interval=5000, wait_retries=120)
    _record("AUTHORIZED_RESOLVED", resolved)

    action = json.loads(contract.action_of(args=[1]).call())
    decision = json.loads(contract.decision_of(args=[1]).call())
    assert action["status"] == "AUTHORIZED"
    assert decision["verdict"] == "AUTHORIZED"
    assert decision["scope_fit"] in ("INSIDE", "OUTSIDE", "AMBIGUOUS")
    assert decision["risk_class"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert len(action["action_hash"]) == 64
    assert contract.is_authorized(args=[1]).call() is True
    assert contract.can_execute(args=[1, action["action_hash"]]).call() is True
    assert contract.can_execute_for(args=[1, action["action_hash"], str(default_account.address)]).call() is True
    assert contract.can_execute_for(args=[1, action["action_hash"], ZERO]).call() is False

    consumed = contract.consume_authorization(args=[1]).transact()
    _record("AUTHORIZED_CONSUMED", consumed)
    assert contract.is_authorized(args=[1]).call() is False
    assert contract.can_execute(args=[1, action["action_hash"]]).call() is False
    assert contract.can_execute_for(args=[1, action["action_hash"], agent]).call() is False

    first_class = contract.propose_action(
        args=[1, "first-class-1", "travel-booking-service", "Purchase a first-class ticket to the approved conference.", '{"fare_class":"first_class","refundability":"refundable"}']
    ).transact()
    _record("OUT_OF_SCOPE_PROPOSED", first_class)
    denied = contract.resolve_action(args=[2]).transact(wait_interval=6000, wait_retries=120)
    _record("OUT_OF_SCOPE_RESOLVED", denied)
    assert json.loads(contract.action_of(args=[2]).call())["status"] == "OUT_OF_SCOPE"
    assert contract.is_authorized(args=[2]).call() is False

    non_refundable = contract.propose_action(
        args=[1, "non-refundable-1", "travel-booking-service", "Purchase a non-refundable economy ticket to the approved conference.", '{"fare_class":"economy","refundability":"non-refundable"}']
    ).transact()
    _record("ESCALATION_PROPOSED", non_refundable)
    escalated = contract.resolve_action(args=[3]).transact(wait_interval=6000, wait_retries=120)
    _record("ESCALATION_RESOLVED", escalated)
    assert json.loads(contract.action_of(args=[3]).call())["status"] == "REQUIRES_ESCALATION"
    approved = contract.resolve_escalation(args=[3, True, "Principal approved the exact non-refundable booking."]).transact()
    _record("PRINCIPAL_RESOLUTION", approved)
    escalation_action = json.loads(contract.action_of(args=[3]).call())
    escalation_decision = json.loads(contract.decision_of(args=[3]).call())
    assert escalation_action["status"] == "AUTHORIZED"
    assert escalation_action["decision_source"] == "PRINCIPAL"
    assert escalation_decision["principal_override"] is True
    assert escalation_decision["principal_approved"] is True
    assert escalation_decision["final_verdict"] == "AUTHORIZED"

    cancellable = contract.propose_action(
        args=[1, "cancel-1", "travel-booking-service", "Book a refundable economy ticket to the approved conference.", '{"fare_class":"economy","refundability":"refundable"}']
    ).transact()
    _record("CANCELLATION_PROPOSED", cancellable)
    cancelled = contract.cancel_action(args=[4, "No longer required."]).transact()
    _record("CANCELLATION", cancelled)
    assert json.loads(contract.action_of(args=[4]).call())["status"] == "CANCELLED"

    second_mandate = contract.create_mandate(
        args=[agent, agent, "Arrange travel only for conferences explicitly approved by the DAO.", "Never buy first-class travel. Never send funds to a personal wallet.", "Escalate non-refundable bookings or unclear conference approval.", 86400]
    ).transact()
    _record("SECOND_MANDATE_CREATED", second_mandate)
    revoked_action = contract.propose_action(
        args=[2, "revocation-1", "travel-booking-service", "Book a refundable economy ticket to an approved conference.", '{"fare_class":"economy","refundability":"refundable"}']
    ).transact()
    _record("REVOCATION_PROPOSED", revoked_action)
    revoked_resolution = contract.resolve_action(args=[5]).transact(wait_interval=6000, wait_retries=120)
    _record("REVOCATION_AUTHORIZED", revoked_resolution)
    assert contract.is_authorized(args=[5]).call() is True
    revoked = contract.revoke_mandate(args=[2, "Mandate withdrawn."]).transact()
    _record("REVOCATION", revoked)
    assert contract.is_authorized(args=[5]).call() is False
    print("LIVE_STATS=" + contract.stats().call())


@pytest.mark.skipif(not os.getenv("MANDATEGUARD_STUDIONET_ADDRESS"), reason="requires existing live contract")
def test_resume_live_cycle(default_account):
    factory = get_contract_factory("MandateGuard")
    contract = factory.build_contract(os.environ["MANDATEGUARD_STUDIONET_ADDRESS"], default_account).connect(default_account)
    agent = str(default_account.address)

    escalated = contract.resolve_action(args=[3]).transact(wait_interval=6000, wait_retries=120)
    _record("ESCALATION_RESOLVED", escalated)
    assert json.loads(contract.action_of(args=[3]).call())["status"] == "REQUIRES_ESCALATION"
    approved = contract.resolve_escalation(args=[3, True, "Principal approved the exact non-refundable booking."]).transact()
    _record("PRINCIPAL_RESOLUTION", approved)
    decision = json.loads(contract.decision_of(args=[3]).call())
    assert decision["principal_override"] is True
    assert decision["principal_approved"] is True
    assert decision["final_verdict"] == "AUTHORIZED"

    cancelled = contract.propose_action(args=[1, "cancel-1", "travel-booking-service", "Book a refundable economy ticket to the approved conference.", '{"fare_class":"economy","refundability":"refundable"}']).transact()
    _record("CANCELLATION_PROPOSED", cancelled)
    cancellation = contract.cancel_action(args=[4, "No longer required."]).transact()
    _record("CANCELLATION", cancellation)
    assert json.loads(contract.action_of(args=[4]).call())["status"] == "CANCELLED"

    mandate = contract.create_mandate(args=[agent, agent, "Arrange travel only for conferences explicitly approved by the DAO.", "Never buy first-class travel. Never send funds to a personal wallet.", "Escalate non-refundable bookings or unclear conference approval.", 86400]).transact()
    _record("SECOND_MANDATE_CREATED", mandate)
    proposed = contract.propose_action(args=[2, "revocation-1", "travel-booking-service", "Book a refundable economy ticket to an approved conference.", '{"fare_class":"economy","refundability":"refundable"}']).transact()
    _record("REVOCATION_PROPOSED", proposed)
    resolved = contract.resolve_action(args=[5]).transact(wait_interval=6000, wait_retries=120)
    _record("REVOCATION_AUTHORIZED", resolved)
    assert contract.is_authorized(args=[5]).call() is True
    revocation = contract.revoke_mandate(args=[2, "Mandate withdrawn."]).transact()
    _record("REVOCATION", revocation)
    assert contract.is_authorized(args=[5]).call() is False
    print("LIVE_STATS=" + contract.stats().call())
