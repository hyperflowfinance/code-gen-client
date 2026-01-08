# codegen

Small Python project that generates an async GraphQL client with
`ariadne-codegen` and a helper script to auto-create operations from a remote
schema.

## What is here

- `graphql/auto.graphql`: auto-generated GraphQL operations.
- `gql_client/`: generated async client package.
- `gen_graphql_ops.py`: introspects a schema endpoint and builds operations.
- `pyproject.toml`: `ariadne-codegen` config (remote schema URL, queries path,
  output package name).

## Regenerate ops and client

1. Ensure the GraphQL endpoint is reachable (default:
   `http://localhost:8000/YOUR_CHAIN/graphql`).
2. Generate operations:
   ```bash
   python gen_graphql_ops.py --url http://localhost:8000/YOUR_CHAIN/graphql --out graphql/auto.graphql --depth 3 
   ```
3. Generate the client:
   ```bash
   ariadne-codegen
   ```
   
## Usage example

```python
import asyncio
from gql_client import Client

async def main():
    client = Client(url="http://localhost:8000/YOUR_CHAIN/graphql")
    data = await client.query_metadata()
    print(data)

asyncio.run(main())
```

## Using env vars for `remote_schema_url`

`ariadne-codegen` does not expand env vars inside `remote_schema_url` in
`pyproject.toml`. If you want the URL built from env, generate a temporary
config file and pass it with `--config`.

Bash example:

```bash
export GRAPHQL_SCHEME=http
export GRAPHQL_HOST=localhost
export GRAPHQL_PORT=8000
export GRAPHQL_CHAIN=your_chain

url="${GRAPHQL_SCHEME}://${GRAPHQL_HOST}:${GRAPHQL_PORT}/${GRAPHQL_CHAIN}/graphql"

cat > pyproject.toml <<EOF
[tool.ariadne-codegen]
remote_schema_url = "${url}"
queries_path = "graphql"
target_package_name = "gql_client"
EOF

ariadne-codegen --config ./pyproject.toml
```

Windows (PowerShell) example

```powershell
$env:GRAPHQL_SCHEME = "http"
$env:GRAPHQL_HOST = "localhost"
$env:GRAPHQL_PORT = "8000"
$env:GRAPHQL_CHAIN = "your_chain"
$url = "$($env:GRAPHQL_SCHEME)://$($env:GRAPHQL_HOST):$($env:GRAPHQL_PORT)/$($env:GRAPHQL_CHAIN)/graphql"

@"
[tool.ariadne-codegen]
remote_schema_url = "$url"
queries_path = "graphql"
target_package_name = "gql_client"
"@ | Set-Content -Path .\pyproject.toml -Encoding utf8

ariadne-codegen --config .\pyproject.toml
```
