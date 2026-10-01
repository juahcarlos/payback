from typing import Any

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.users import UserCreateModel, UserReadModel
from app.domain.users import UserPaymentInputData
from app.models import Users
from app.repositories.users import UserDBRepo


class FakeTransaction:
    def __init__(self, session: "FakeSession") -> None:
        self.session = session

    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, exc_type: Any, *_: object) -> None:
        if exc_type is None and self.session.commit_error is not None:
            raise self.session.commit_error


class FakeSession:
    def __init__(self, commit_error: Exception | None = None) -> None:
        self.commit_error = commit_error
        self.user: Any = None

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    def begin(self) -> FakeTransaction:
        return FakeTransaction(self)

    def add(self, user: Any) -> None:
        self.user = user

    async def flush(self) -> None:
        self.user.id = 42


@pytest.mark.anyio
async def test_create_user_inserts_and_sets_cn_in_one_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = UserDBRepo()
    session = FakeSession()
    monkeypatch.setattr(repo, "create_session", lambda: session)

    user = await repo.create_user(UserCreateModel(email="new@example.com"))

    assert user is not None
    assert user.id == 42
    assert user.email == "new@example.com"
    assert user.cn == "sec42"


@pytest.mark.anyio
async def test_create_user_returns_existing_user_after_unique_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = UserDBRepo()
    existing_user = UserReadModel(email="existing@example.com", id=7)
    duplicate_error = IntegrityError("INSERT", {}, Exception("duplicate email"))
    monkeypatch.setattr(repo, "create_session", lambda: FakeSession(duplicate_error))
    get_user = AsyncMock(return_value=existing_user)
    monkeypatch.setattr(repo, "get_user_by_email", get_user)

    result = await repo.create_user(UserCreateModel(email="existing@example.com"))

    assert result is existing_user
    get_user.assert_awaited_once_with("existing@example.com")


def test_user_email_models_normalize_email() -> None:
    assert UserCreateModel(email="  User@Test.com ").email == "user@test.com"
    assert UserReadModel(email=" User@Test.com ", id=1).email == "user@test.com"
    assert UserPaymentInputData(
        email=" User@Test.com ",
        country_iso="us",
        amount=1,
    ).email == "user@test.com"


def test_email_has_unique_database_index() -> None:
    unique_indexes = {
        tuple(column.name for column in index.columns)
        for index in Users.__table__.indexes
        if index.unique
    }

    assert ("email",) in unique_indexes
    assert ("code",) in unique_indexes
    assert ("cn",) in unique_indexes
    assert Users.__table__.c.email.type.length == 250
