import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import delete

from app.core.database import create_session
from app.models import ServersConfig, VpnServersStat
from app.repositories.servers import ServerDBRepo


@pytest.mark.anyio
async def test_servers_without_stats_are_counted_as_offline(
    unpooled_test_database,
) -> None:
    token = uuid4().hex[:16]
    server = f"test-{token}-offline"
    repo = ServerDBRepo()
    try:
        before = await asyncio.wait_for(repo.get_servers_stat(), timeout=10)
    except TimeoutError:
        pytest.fail("Initial get_servers_stat() call timed out after 10 seconds")
    assert before is not None

    try:
        async with create_session() as session:
            async with session.begin():
                session.add(ServersConfig(server=server, remote_ips="[]"))

        try:
            stats = await asyncio.wait_for(repo.get_servers_stat(), timeout=10)
        except TimeoutError:
            pytest.fail("get_servers_stat() after test server insert timed out after 10 seconds")
        assert stats is not None
        assert stats.total == before.total + 1
        assert stats.offline == before.offline + 1
        assert stats.online == before.online
    finally:
        async with create_session() as session:
            async with session.begin():
                await session.execute(
                    delete(VpnServersStat).where(VpnServersStat.server == server)
                )
                await session.execute(
                    delete(ServersConfig).where(ServersConfig.server == server)
                )
