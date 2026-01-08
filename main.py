import asyncio
from gql_client import Client

async def main():
    client = Client(url="http://localhost:8000/anvil/graphql")
    data = await client.query_metadata()
    print(data)

asyncio.run(main())