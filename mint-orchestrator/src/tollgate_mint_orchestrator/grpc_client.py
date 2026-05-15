import logging
from typing import Optional

import grpc.aio

logger = logging.getLogger(__name__)

try:
    from tollgate_mint_orchestrator import management_pb2
    from tollgate_mint_orchestrator import management_pb2_grpc

    HAS_GRPC_STUBS = True
except ImportError:
    HAS_GRPC_STUBS = False
    logger.warning("gRPC stubs not generated yet, using stub implementations")


class MintGrpcClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub = None

    async def connect(self):
        target = f"{self.host}:{self.port}"
        self.channel = grpc.aio.insecure_channel(target)
        if HAS_GRPC_STUBS:
            self.stub = management_pb2_grpc.MintStub(self.channel)
        logger.info(f"Connected to mint gRPC at {target}")

    async def close(self):
        if self.channel:
            await self.channel.close()
            self.channel = None
            self.stub = None

    async def update_nut04_quote(self, quote_id: str, state: str) -> bool:
        if not self.stub:
            logger.error("gRPC stub not connected")
            return False
        try:
            request = management_pb2.UpdateQuoteRequest(quote_id=quote_id, state=state)
            await self.stub.UpdateNut04Quote(request)
            logger.info(f"Updated quote {quote_id} to state {state}")
            return True
        except grpc.aio.AioRpcError as e:
            logger.error(f"gRPC error updating quote {quote_id}: {e.code()} - {e.details()}")
            return False

    async def get_nut04_quote(self, quote_id: str) -> Optional[dict]:
        if not self.stub:
            return None
        try:
            request = management_pb2.GetNut04QuoteRequest(quote_id=quote_id)
            response = await self.stub.GetNut04Quote(request)
            quote = response.quote
            return {
                "quote": quote.quote,
                "method": quote.method,
                "request": quote.request,
                "checking_id": quote.checking_id,
                "unit": quote.unit,
                "amount": quote.amount,
                "state": quote.state,
                "created_time": quote.created_time,
                "paid_time": quote.paid_time,
                "expiry": quote.expiry,
            }
        except grpc.aio.AioRpcError as e:
            logger.error(f"gRPC error getting quote {quote_id}: {e.code()}")
            return None

    async def get_info(self) -> Optional[dict]:
        if not self.stub:
            return None
        try:
            response = await self.stub.GetInfo(management_pb2.GetInfoRequest())
            return {
                "name": response.name,
                "pubkey": response.pubkey,
                "version": response.version,
                "description": response.description,
            }
        except grpc.aio.AioRpcError:
            return None
