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
    client = Client(url="http://localhost:8000/anvil/graphql")
    data = await client.query_metadata()
    print(data)

asyncio.run(main())
```
