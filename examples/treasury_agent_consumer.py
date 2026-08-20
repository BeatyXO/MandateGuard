# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

import json


@gl.contract_interface
class IMandateGuard:
    class View:
        pass

    class Write:
        def can_execute_for(self, mandate_id: u256, action_hash: str, expected_consumer: Address) -> bool:
            pass

        def compute_action_hash(self, mandate_id: u256, agent: Address, action_nonce: str, target: str, action_description: str, action_payload: str) -> str:
            pass

        def consume_authorization(self, action_id: u256) -> None:
            pass

        def action_of(self, action_id: u256) -> str:
            pass


class TreasuryAgentConsumer(gl.Contract):
    guard: Address
    executed: TreeMap[str, bool]
    execution_log: TreeMap[str, str]

    def __init__(self, guard: Address) -> None:
        self.guard = guard if isinstance(guard, Address) else Address(guard)
        self.executed = TreeMap[str, bool]()
        self.execution_log = TreeMap[str, str]()

    @gl.public.write
    def execute_authorized_action(self, action_id: u256, mandate_id: u256, agent: Address, action_nonce: str, target: str, action_description: str, action_payload: str) -> None:
        key = str(action_id)
        if key in self.executed and self.executed[key]:
            raise gl.vm.UserError("EXPECTED: action already executed")

        guard = gl.get_contract_at(self.guard, IMandateGuard)
        expected_hash = guard.compute_action_hash(mandate_id, agent, action_nonce, target, action_description, action_payload)
        if not guard.can_execute_for(mandate_id, expected_hash, self.address):
            raise gl.vm.UserError("EXPECTED: MandateGuard authorization required")

        action = json.loads(guard.action_of(action_id))
        if str(action["action_hash"]).lower() != expected_hash.lower():
            raise gl.vm.UserError("EXPECTED: action hash mismatch")

        # Real consumers perform deterministic execution here: amount checks,
        # allowlists, accounting, transfers, signatures, etc.
        self.executed[key] = True
        self.execution_log[key] = json.dumps(
            {
                "action_hash": str(action["action_hash"]),
                "target": str(action["target"]),
                "executed": True,
            },
            sort_keys=True,
        )
        guard.consume_authorization(action_id)

    @gl.public.view
    def was_executed(self, action_id: u256) -> bool:
        key = str(action_id)
        return key in self.executed and self.executed[key]

    @gl.public.view
    def execution_of(self, action_id: u256) -> str:
        key = str(action_id)
        if key not in self.execution_log:
            return "{}"
        return self.execution_log[key]
