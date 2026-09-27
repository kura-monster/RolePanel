import aiosqlite
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "rolepanel.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS panels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER UNIQUE,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                color INTEGER NOT NULL DEFAULT 3447003
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS panel_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                panel_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                emoji TEXT,
                description TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (panel_id) REFERENCES panels(id) ON DELETE CASCADE,
                UNIQUE(panel_id, role_id)
            )
        """)
        await db.commit()


async def create_panel(guild_id: int, channel_id: int, title: str, description: str = "", color: int = 3447003) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO panels (guild_id, channel_id, title, description, color) VALUES (?, ?, ?, ?, ?)",
            (guild_id, channel_id, title, description, color),
        )
        await db.commit()
        return cursor.lastrowid


async def update_panel_message_id(panel_id: int, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE panels SET message_id = ? WHERE id = ?", (message_id, panel_id))
        await db.commit()


async def update_panel(panel_id: int, *, title: str = None, description: str = None, color: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if title is not None:
            await db.execute("UPDATE panels SET title = ? WHERE id = ?", (title, panel_id))
        if description is not None:
            await db.execute("UPDATE panels SET description = ? WHERE id = ?", (description, panel_id))
        if color is not None:
            await db.execute("UPDATE panels SET color = ? WHERE id = ?", (color, panel_id))
        await db.commit()


async def delete_panel(panel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM panel_roles WHERE panel_id = ?", (panel_id,))
        await db.execute("DELETE FROM panels WHERE id = ?", (panel_id,))
        await db.commit()


async def get_panel(panel_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM panels WHERE id = ?", (panel_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


async def get_panel_by_message(message_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM panels WHERE message_id = ?", (message_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


async def get_panels_for_guild(guild_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM panels WHERE guild_id = ? ORDER BY id", (guild_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def add_role_to_panel(panel_id: int, role_id: int, label: str, emoji: str = None, description: str = "") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO panel_roles (panel_id, role_id, label, emoji, description) VALUES (?, ?, ?, ?, ?)",
            (panel_id, role_id, label, emoji, description),
        )
        await db.commit()
        return cursor.lastrowid


async def remove_role_from_panel(panel_id: int, role_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM panel_roles WHERE panel_id = ? AND role_id = ?",
            (panel_id, role_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_roles_for_panel(panel_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM panel_roles WHERE panel_id = ? ORDER BY id", (panel_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_all_panels_with_messages(guild_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM panels WHERE guild_id = ? AND message_id IS NOT NULL ORDER BY id",
            (guild_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
