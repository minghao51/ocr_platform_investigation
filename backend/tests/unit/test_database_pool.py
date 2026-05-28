import pytest


class TestConnectionWrapper:
    def test_init(self, tmp_path):
        from database.pool import ConnectionWrapper

        db_path = tmp_path / "test.db"
        wrapper = ConnectionWrapper(db_path)
        assert wrapper.db_path == db_path
        assert wrapper._connection is None

    @pytest.mark.asyncio
    async def test_aenter_creates_connection(self, tmp_path):
        from database.pool import ConnectionWrapper

        db_path = tmp_path / "test.db"
        wrapper = ConnectionWrapper(db_path)

        conn = await wrapper.__aenter__()
        assert conn is not None
        assert wrapper._connection is not None
        assert db_path.exists()

        await wrapper.__aexit__(None, None, None)
        assert wrapper._connection is None

    @pytest.mark.asyncio
    async def test_connection_sets_row_factory(self, tmp_path):
        from database.pool import ConnectionWrapper
        import aiosqlite

        db_path = tmp_path / "test.db"
        wrapper = ConnectionWrapper(db_path)

        conn = await wrapper.__aenter__()
        assert conn.row_factory is aiosqlite.Row

        await wrapper.__aexit__(None, None, None)

    @pytest.mark.asyncio
    async def test_double_enter_exit(self, tmp_path):
        from database.pool import ConnectionWrapper

        db_path = tmp_path / "test.db"
        wrapper = ConnectionWrapper(db_path)

        conn1 = await wrapper.__aenter__()
        await wrapper.__aexit__(None, None, None)
        assert wrapper._connection is None

        conn2 = await wrapper.__aenter__()
        assert conn2 is not None
        assert conn2 is not conn1

        await wrapper.__aexit__(None, None, None)


class TestConnect:
    @pytest.mark.asyncio
    async def test_connect_with_custom_path(self, tmp_path):
        from database.pool import connect

        db_path = tmp_path / "custom.db"
        async with connect(db_path) as db:
            cursor = await db.execute("SELECT 1")
            row = await cursor.fetchone()
            assert row[0] == 1

    @pytest.mark.asyncio
    async def test_connect_executes_pragmas(self, tmp_path):
        from database.pool import connect

        db_path = tmp_path / "pragma.db"
        async with connect(db_path) as db:
            cursor = await db.execute("PRAGMA journal_mode")
            row = await cursor.fetchone()
            assert row[0] == "wal"


class TestClosePool:
    @pytest.mark.asyncio
    async def test_close_pool_is_noop(self):
        from database.pool import close_pool

        result = await close_pool()
        assert result is None
