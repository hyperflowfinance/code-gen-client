import inspect
from dataclasses import dataclass
from typing import Any

from gql_client import Client

from ..config import Settings


def _serialize(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj


def _filter_kwargs(callable_, kwargs: dict[str, Any]) -> dict[str, Any]:
    signature = inspect.signature(callable_)
    allowed: set[str] = set()
    for name, param in signature.parameters.items():
        if name == "self":
            continue
        if param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):
            allowed.add(name)
    return {key: value for key, value in kwargs.items() if key in allowed}


@dataclass(frozen=True)
class GraphQLService:
    settings: Settings

    async def _call(self, client: Client, names: list[str], **kwargs: Any) -> Any:
        for name in names:
            if hasattr(client, name):
                method = getattr(client, name)
                filtered = _filter_kwargs(method, kwargs)
                return await method(**filtered)
        raise RuntimeError("No matching client method found.")

    async def get_metadata(self) -> Any:
        async with Client(url=self.settings.graphql_url) as client:
            result = await self._call(client, ["get_metadata", "query_metadata"])
            return _serialize(result)

    async def get_usage(self) -> Any:
        async with Client(url=self.settings.graphql_url) as client:
            result = await self._call(client, ["get_usage", "query_usage_stat"])
            return _serialize(result)

    async def web3_sha3(self, message: str) -> Any:
        async with Client(url=self.settings.graphql_url) as client:
            result = await self._call(
                client, ["web3_sha3", "query_web_3_sha_3"], message=message
            )
            return _serialize(result)

    async def send_raw(self, signed_tx: str) -> Any:
        async with Client(url=self.settings.graphql_url) as client:
            result = await self._call(
                client,
                ["send_raw", "mutation_send_raw_transaction"],
                signed_tx=signed_tx,
            )
            return _serialize(result)
