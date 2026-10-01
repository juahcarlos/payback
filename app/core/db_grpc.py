from dataclasses import dataclass

import betterproto
import grpclib
from betterproto.grpc.grpclib_server import ServiceBase
from grpclib import GRPCError, const


@dataclass(eq=False, repr=False)
class EndpointRequest(betterproto.Message):
    test: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class EndpointResponse(betterproto.Message):
    test_res: str = betterproto.string_field(1)


class TestStub(betterproto.ServiceStub):
    async def test(self, *, test: str) -> "EndpointResponse":
        request = EndpointRequest()
        request.test = test

        return await self._unary_unary("/Test/test", request, EndpointResponse)


class TestBase(ServiceBase):
    async def test(self, test: str) -> "EndpointResponse":
        raise GRPCError(const.Status.UNIMPLEMENTED)

    async def __rpc_test(
            self,
            stream: grpclib.server.Stream,
    ) -> None:
        request: EndpointRequest | None = await stream.recv_message()  # type: ignore[attr-defined]

        if not request:
            return

        request_kwargs = {
            "test": request.test,
        }

        response = await self.test(**request_kwargs)
        await stream.send_message(response)  # type: ignore[attr-defined]

    def __mapping__(self) -> dict[str, const.Handler]:
        return {
            "/Test/test": const.Handler(
                self.__rpc_test,
                const.Cardinality.UNARY_UNARY,
                EndpointRequest,
                EndpointResponse,
            ),
        }
