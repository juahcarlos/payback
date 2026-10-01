from unittest.mock import AsyncMock

import pytest

from app.domain.buy_form_filling import BuyFormFillingSaveModel
from app.domain.transactions import TransactionSaveModel
from app.repositories.buy_form_filling import BuyFormFillingDBRepo
from app.repositories.transactions import TransactionDBRepo
from app.utils.email import normalize_email


def test_normalize_email_trims_and_lowercases() -> None:
    assert normalize_email("  User+Tag@Example.COM \t") == "user+tag@example.com"


@pytest.mark.anyio
async def test_transaction_insert_uses_normalized_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = TransactionDBRepo()
    insert_with_primary_key = AsyncMock(return_value=123)
    monkeypatch.setattr(repo, "insert_with_primary_key", insert_with_primary_key)

    transaction_id = await repo.insert_transaction(
        TransactionSaveModel(days=30, amount=10, email=" User@Example.COM ")
    )

    statement = insert_with_primary_key.await_args.args[0]
    assert statement.compile().params["email"] == "user@example.com"
    assert transaction_id == 123


@pytest.mark.anyio
async def test_buy_form_insert_and_update_use_normalized_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = BuyFormFillingDBRepo()
    insert_only = AsyncMock()
    update_only = AsyncMock()
    monkeypatch.setattr(repo, "insert_only", insert_only)
    monkeypatch.setattr(repo, "get_filling_by_max_id", AsyncMock(return_value=None))
    monkeypatch.setattr(repo, "update_only", update_only)

    await repo.insert_filling(BuyFormFillingSaveModel(email=" User@Example.COM "))
    await repo.update_filling(1, " User@Example.COM ")

    insert_statement = insert_only.await_args.args[0]
    update_statement = update_only.await_args.args[0]
    assert insert_statement.compile().params["email"] == "user@example.com"
    assert update_statement.compile().params["email"] == "user@example.com"
