import asyncio
import json
import logging
import os
import signal
from dataclasses import asdict

from tollgate_mint_orchestrator.api import OrchestratorAPI
from tollgate_mint_orchestrator.audit_log import AuditLogger
from tollgate_mint_orchestrator.event_validator import EventValidator
from tollgate_mint_orchestrator.grpc_client import MintGrpcClient
from tollgate_mint_orchestrator.mint_registry import MintRegistry
from tollgate_mint_orchestrator.nostr_subscriber import NostrSubscriber

logger = logging.getLogger(__name__)

DEFAULTS = {
    "ORCHESTRATOR_RELAY_URL": "ws://localhost:7777",
    "ORCHESTRATOR_REGISTRY_PATH": "/opt/tollgate/mints/registry.json",
    "ORCHESTRATOR_AUDIT_LOG_PATH": "/var/log/tollgate/mint-approvals.jsonl",
    "ORCHESTRATOR_API_HOST": "0.0.0.0",
    "ORCHESTRATOR_API_PORT": "8090",
    "ORCHESTRATOR_APPROVAL_TTL_SECS": "300",
    "ORCHESTRATOR_LOG_LEVEL": "info",
}

_grpc_clients: dict[str, MintGrpcClient] = {}


def _env(key: str) -> str:
    return os.environ.get(key, DEFAULTS[key])


async def _get_grpc_client(mint_entry) -> MintGrpcClient:
    key = mint_entry.subdomain
    if key not in _grpc_clients:
        client = MintGrpcClient("localhost", mint_entry.grpc_port)
        await client.connect()
        _grpc_clients[key] = client
    return _grpc_clients[key]


async def _handle_event(
    event: dict,
    validator: EventValidator,
    registry: MintRegistry,
    audit: AuditLogger,
):
    result = validator.validate(event)
    if not result.valid:
        logger.warning(f"Invalid approval event: {result.error}")
        audit.log_approval(
            event_id=event.get("id", ""),
            npub=event.get("pubkey", ""),
            mint_url="",
            quote_id="",
            amount=0,
            unit="",
            success=False,
            error=result.error,
        )
        return

    mint_data = result.mint
    from tollgate_mint_orchestrator.mint_registry import MintEntry
    mint_entry = MintEntry(**mint_data)

    client = await _get_grpc_client(mint_entry)

    quote = await client.get_nut04_quote(result.quote_id)
    if not quote:
        error = f"Quote {result.quote_id} not found on mint {mint_entry.url}"
        logger.error(error)
        audit.log_approval(
            event_id=event.get("id", ""),
            npub=event.get("pubkey", ""),
            mint_url=mint_entry.url,
            quote_id=result.quote_id,
            amount=result.amount,
            unit=result.unit,
            success=False,
            error=error,
        )
        return

    if quote.get("state") not in ("UNPAID", None):
        error = f"Quote {result.quote_id} is {quote.get('state')}, not UNPAID"
        logger.warning(error)
        audit.log_approval(
            event_id=event.get("id", ""),
            npub=event.get("pubkey", ""),
            mint_url=mint_entry.url,
            quote_id=result.quote_id,
            amount=result.amount,
            unit=result.unit,
            success=False,
            error=error,
        )
        return

    success = await client.update_nut04_quote(result.quote_id, "PAID")
    audit.log_approval(
        event_id=event.get("id", ""),
        npub=event.get("pubkey", ""),
        mint_url=mint_entry.url,
        quote_id=result.quote_id,
        amount=result.amount,
        unit=result.unit,
        success=success,
        error=None if success else "gRPC update failed",
    )
    if success:
        logger.info(
            f"Approved quote {result.quote_id} for {result.amount} {result.unit} on {mint_entry.url}"
        )


async def run_daemon():
    log_level = getattr(logging, _env("ORCHESTRATOR_LOG_LEVEL").upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    registry = MintRegistry.load(_env("ORCHESTRATOR_REGISTRY_PATH"))
    audit = AuditLogger(_env("ORCHESTRATOR_AUDIT_LOG_PATH"))
    validator = EventValidator(registry, int(_env("ORCHESTRATOR_APPROVAL_TTL_SECS")))

    filters = [{"kinds": [38010], "#t": ["mint-approval"]}]
    subscriber = NostrSubscriber(_env("ORCHESTRATOR_RELAY_URL"), filters)

    api = OrchestratorAPI(
        registry,
        audit,
        host=_env("ORCHESTRATOR_API_HOST"),
        port=int(_env("ORCHESTRATOR_API_PORT")),
    )

    await api.start()

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _signal_handler():
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    subscriber_task = asyncio.create_task(
        subscriber.start(
            lambda e: _handle_event(e, validator, registry, audit)
        )
    )

    try:
        await stop_event.wait()
    finally:
        await subscriber.stop()
        subscriber_task.cancel()
        try:
            await subscriber_task
        except asyncio.CancelledError:
            pass
        for client in _grpc_clients.values():
            await client.close()
        _grpc_clients.clear()
        await api.stop()


def main():
    asyncio.run(run_daemon())


if __name__ == "__main__":
    main()
