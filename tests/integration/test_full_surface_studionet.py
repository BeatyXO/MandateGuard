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


def test_full_surface_on_studionet(default_account):
    factory = get_contract_factory("MandateGuard")
    contract = factory.deploy(account=default_account).connect(default_account)
    agent = str(default_account.address)

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
    assert tx_execution_succeeded(created)

    opened = contract.propose_action(
        args=[
            1,
            "authorized-1",
            "travel-booking-service",
            "Book a refundable economy ticket to an approved conference.",
            '{"fare_class":"economy","refundability":"refundable"}',
        ]
    ).transact()
    assert tx_execution_succeeded(opened)

    resolved = contract.resolve_action(args=[1]).transact(wait_interval=5000, wait_retries=120)
    assert tx_execution_succeeded(resolved)

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
