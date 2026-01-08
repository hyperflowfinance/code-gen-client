import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


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


def build_graphql_url(
    scheme: str,
    host: str,
    port: str | None,
    chain: str | None,
    path: str | None,
) -> str:
    if not host:
        raise RuntimeError("Set GRAPHQL_HOST in .env")

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


@dataclass(frozen=True)
class Settings:
    graphql_scheme: str
    graphql_host: str
    graphql_port: str | None
    graphql_chain: str | None
    graphql_path: str | None
    graphql_url: str


def get_settings() -> Settings:
    load_env()
    scheme = os.getenv("GRAPHQL_SCHEME", "http")
    host = os.getenv("GRAPHQL_HOST", "")
    port = os.getenv("GRAPHQL_PORT")
    chain = os.getenv("GRAPHQL_CHAIN")
    path = os.getenv("GRAPHQL_PATH")
    url = build_graphql_url(
        scheme=scheme, host=host, port=port, chain=chain, path=path
    )
    return Settings(
        graphql_scheme=scheme,
        graphql_host=host,
        graphql_port=port,
        graphql_chain=chain,
        graphql_path=path,
        graphql_url=url,
    )
