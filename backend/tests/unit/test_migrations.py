import pytest
import aiosqlite


class TestMigrationHelpers:
    @pytest.mark.asyncio
    async def test_check_table_returns_false_for_nonexistent(self):
        from database.migrations import _check_table

        async with aiosqlite.connect(":memory:") as db:
            result = await _check_table(db, "nonexistent")
            assert result is False

    @pytest.mark.asyncio
    async def test_check_table_returns_true_for_existing(self):
        from database.migrations import _check_table

        async with aiosqlite.connect(":memory:") as db:
            await db.execute("CREATE TABLE test_table (id INTEGER)")
            result = await _check_table(db, "test_table")
            assert result is True

    @pytest.mark.asyncio
    async def test_check_column_returns_false_for_missing(self):
        from database.migrations import _check_column

        async with aiosqlite.connect(":memory:") as db:
            await db.execute("CREATE TABLE test_table (id INTEGER)")
            result = await _check_column(db, "test_table", "name")
            assert result is False

    @pytest.mark.asyncio
    async def test_check_column_returns_true_for_existing(self):
        from database.migrations import _check_column

        async with aiosqlite.connect(":memory:") as db:
            await db.execute("CREATE TABLE test_table (id INTEGER, name TEXT)")
            result = await _check_column(db, "test_table", "name")
            assert result is True

    @pytest.mark.asyncio
    async def test_add_column_adds_new_column(self):
        from database.migrations import _check_column, _add_column

        async with aiosqlite.connect(":memory:") as db:
            await db.execute("CREATE TABLE test_table (id INTEGER)")
            await _add_column(db, "test_table", "name", "TEXT")
            assert await _check_column(db, "test_table", "name") is True

    @pytest.mark.asyncio
    async def test_add_column_skips_existing(self):
        from database.migrations import _add_column

        async with aiosqlite.connect(":memory:") as db:
            await db.execute("CREATE TABLE test_table (id INTEGER, name TEXT)")
            await _add_column(db, "test_table", "name", "TEXT")


class TestMigrationsTable:
    @pytest.mark.asyncio
    async def test_ensure_migrations_table_creates(self):
        from database.migrations import _ensure_migrations_table, _check_table

        async with aiosqlite.connect(":memory:") as db:
            await _ensure_migrations_table(db)
            assert await _check_table(db, "_migrations") is True

    @pytest.mark.asyncio
    async def test_is_migration_applied_returns_false_initially(self):
        from database.migrations import _ensure_migrations_table, _is_migration_applied

        async with aiosqlite.connect(":memory:") as db:
            await _ensure_migrations_table(db)
            result = await _is_migration_applied(db, "test_migration")
            assert result is False

    @pytest.mark.asyncio
    async def test_record_and_check_migration(self):
        from database.migrations import (
            _ensure_migrations_table,
            _record_migration,
            _is_migration_applied,
        )

        async with aiosqlite.connect(":memory:") as db:
            await _ensure_migrations_table(db)
            await _record_migration(db, "test_migration")
            assert await _is_migration_applied(db, "test_migration") is True


class TestMigrationDataclass:
    def test_migration_dataclass(self):
        from database.migrations import Migration

        migration = Migration("test", lambda db: None)
        assert migration.name == "test"
        assert callable(migration.up)


class TestMigrationsList:
    def test_migrations_list_is_populated(self):
        from database.migrations import MIGRATIONS

        assert len(MIGRATIONS) > 0
        names = [m.name for m in MIGRATIONS]
        assert "init_database" in names
        assert "users_table" in names
        assert all(m.name and callable(m.up) for m in MIGRATIONS)
