from typing import Callable, Generator

import pytest

from app.main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def override_depends() -> Generator[Callable, None, None]:
    app.dependency_overrides = {}

    def _override(dep: Callable, value: Callable) -> None:
        app.dependency_overrides[dep] = value

    yield _override

    app.dependency_overrides = {}
