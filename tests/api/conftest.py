from contextlib import asynccontextmanager
from typing import AsyncGenerator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.main import app


def message() -> str:
    return "Mock message"


@pytest.fixture()
def mock_message() -> str:
    return message()


@asynccontextmanager
async def test_lifespan(app: FastAPI):
    class MockTransaltionService:
        def translate_message(self, key: str, locale: str = "en") -> str:
            return message()

    app.state.i18n = MockTransaltionService()
    yield


@pytest.fixture()
async def async_client() -> AsyncGenerator[AsyncClient]:
    app.router.lifespan_context = test_lifespan

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
