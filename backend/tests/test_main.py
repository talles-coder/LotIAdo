"""Tests for the app's HTTP client test fixture."""
from httpx import AsyncClient


async def test_health_check(client: AsyncClient):
    """The health endpoint responds via the ASGI test client."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
