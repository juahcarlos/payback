from httpx import AsyncClient


async def test_ping(async_client: AsyncClient):
    response = await async_client.get("/ping")

    assert response.status_code == 200
    assert response.json() == {"ping": "pong!!"}


async def test_exceptions(async_client: AsyncClient):
    pass
