from unittest.mock import AsyncMock

import pytest

from app.domain.emails import RestoreCodeData
from app.domain.users import UserReadModel
from app.services.code import CodeService


@pytest.mark.anyio
@pytest.mark.parametrize(
    "user",
    [
        None,
        UserReadModel(id=1, email="user@example.com", code=""),
        UserReadModel(id=1, email="user@example.com", code="KEYTEST", expires=1),
    ],
)
async def test_recovery_returns_same_response_for_ineligible_accounts(user) -> None:
    user_repo = AsyncMock()
    user_repo.get_user_by_email.return_value = user
    email_service = AsyncMock()
    redis = AsyncMock()
    redis.eval.return_value = 1
    service = CodeService(user_repo, email_service, redis)

    result = await service.restore_access_code("user@example.com", "192.0.2.1")

    assert result == RestoreCodeData(email="user@example.com", status="OK")
    redis.eval.assert_awaited_once()
    email_service.send_restore_email.assert_not_awaited()
