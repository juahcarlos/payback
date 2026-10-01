from unittest.mock import AsyncMock

import pytest

from app.schemas.servers import AdminServerPatchRequest
from app.services.servers import ServerService


@pytest.mark.anyio
async def test_partially_update_server_applies_false_values() -> None:
    repo = AsyncMock()
    service = ServerService(
        repo=repo,
        ipinfo_service=None,
        translation_service=None,
        locale="en",
    )

    await service.partially_update_server(
        server_id=1,
        data=AdminServerPatchRequest(visible=False, sync=False),
    )

    repo.update_server.assert_awaited_once_with(
        server_id=1,
        data={"hidden": True, "enabled": False},
    )


@pytest.mark.anyio
async def test_partially_update_server_ignores_null_values() -> None:
    repo = AsyncMock()
    service = ServerService(
        repo=repo,
        ipinfo_service=None,
        translation_service=None,
        locale="en",
    )

    await service.partially_update_server(
        server_id=1,
        data=AdminServerPatchRequest(visible=None, sync=None),
    )

    repo.update_server.assert_awaited_once_with(server_id=1, data={})
