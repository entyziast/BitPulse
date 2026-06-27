import grpc
from rate_limiter_pb2_grpc import RateLimiterStub
from rate_limiter_pb2 import RequestIP

class RateLimiterClient:
    def __init__(self, address):
        self.channel = grpc.aio.insecure_channel(address)
        self.stub = RateLimiterStub(self.channel)

    async def check_access(self, ip, timeout=0.1) -> bool:
        try:
            response = await self.stub.CheckAccess(request=RequestIP(ip=ip), timeout=timeout)
            return response.access
        except grpc.RpcError:
            print("Error in RateLimiterClient, goRateLimiter is not available")
            return True
    
    async def close(self):
        await self.channel.close()