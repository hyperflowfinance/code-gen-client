import asyncio
import os
from pathlib import Path
from urllib.parse import urlparse

from gql_client import Client


def load_env(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            os.environ.setdefault(key, value)


def get_graphql_url() -> str:
    scheme = os.getenv("GRAPHQL_SCHEME", "http")
    host = os.getenv("GRAPHQL_HOST")
    if not host:
        raise RuntimeError("Set GRAPHQL_HOST in .env")
    port = os.getenv("GRAPHQL_PORT")
    path = os.getenv("GRAPHQL_PATH")
    chain = os.getenv("GRAPHQL_CHAIN")

    if not path:
        if not chain:
            raise RuntimeError("Set GRAPHQL_PATH or GRAPHQL_CHAIN in .env")
        path = f"{chain.strip('/')}/graphql"

    if "://" in host:
        parsed = urlparse(host)
        base_scheme = parsed.scheme or scheme
        base_host = parsed.hostname or host
        base_port = parsed.port or (int(port) if port else None)
    else:
        base_scheme = scheme
        base_host = host
        base_port = int(port) if port else None

    if not base_host:
        raise RuntimeError("Invalid GRAPHQL_HOST value")

    if base_port:
        base = f"{base_scheme}://{base_host}:{base_port}"
    else:
        base = f"{base_scheme}://{base_host}"
    return f"{base}/{path.lstrip('/')}"

async def main():
    load_env()
    client = Client(url=get_graphql_url())
    data = await client.query_metadata()
    print(data)

asyncio.run(main())
