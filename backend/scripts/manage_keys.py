#!/usr/bin/env python3
"""API Key管理CLI工具

用法:
    python manage_keys.py create <name> [rate_limit]
    python manage_keys.py list
    python manage_keys.py revoke <key_prefix>
"""

import asyncio
import secrets
import sys
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent.parent / "api_keys.db"


async def ensure_db():
    """确保数据库和表存在"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                rate_limit INTEGER DEFAULT 60,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def create_key(name: str, rate_limit: int = 60) -> str:
    """创建新的API Key"""
    key = f"sk-{secrets.token_hex(32)}"
    await ensure_db()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO api_keys (key, name, rate_limit) VALUES (?, ?, ?)",
            (key, name, rate_limit),
        )
        await db.commit()
    print(f"✅ Created API Key for '{name}':")
    print(f"   Key: {key}")
    print(f"   Rate limit: {rate_limit}/min")
    return key


async def list_keys():
    """列出所有API Key"""
    await ensure_db()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT key, name, rate_limit, is_active, created_at FROM api_keys ORDER BY created_at"
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        print("No API keys found.")
        return

    print(f"{'Status':<8} {'Name':<20} {'Key':<18} {'Limit':<8} {'Created'}")
    print("-" * 70)
    for row in rows:
        status = "✅" if row[3] else "❌"
        key_preview = row[0][:12] + "..."
        print(f"{status:<8} {row[1]:<20} {key_preview:<18} {row[2]}/min   {row[4]}")


async def revoke_key(key_prefix: str):
    """撤销指定Key（通过前缀匹配）"""
    await ensure_db()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE api_keys SET is_active = 0 WHERE key LIKE ?",
            (f"{key_prefix}%",),
        )
        await db.commit()
        if cursor.rowcount > 0:
            print(f"✅ Revoked {cursor.rowcount} key(s) matching '{key_prefix}*'")
        else:
            print(f"❌ No active keys matching '{key_prefix}*'")


def main():
    if len(sys.argv) < 2:
        print("Usage: python manage_keys.py <create|list|revoke> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "create":
        name = sys.argv[2] if len(sys.argv) > 2 else "default"
        rate = int(sys.argv[3]) if len(sys.argv) > 3 else 60
        asyncio.run(create_key(name, rate))
    elif cmd == "list":
        asyncio.run(list_keys())
    elif cmd == "revoke":
        if len(sys.argv) < 3:
            print("Usage: python manage_keys.py revoke <key_prefix>")
            sys.exit(1)
        asyncio.run(revoke_key(sys.argv[2]))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()