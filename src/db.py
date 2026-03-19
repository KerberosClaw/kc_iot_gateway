"""
SQLite 資料層 — 告警規則 + 告警歷史
"""

import json
import time
import aiosqlite
import logging

log = logging.getLogger("db")

DB_PATH = "gateway.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                name TEXT PRIMARY KEY,
                description TEXT,
                device TEXT,
                condition TEXT,
                severity TEXT DEFAULT 'info',
                cooldown INTEGER DEFAULT 300,
                actions TEXT,
                active INTEGER DEFAULT 1,
                created_at REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT,
                device_id TEXT,
                severity TEXT,
                message TEXT,
                value TEXT,
                created_at REAL
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(created_at DESC)
        """)
        await db.commit()
    log.info("Database initialized")


# --- Rules CRUD ---

async def load_rules() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM rules") as cursor:
            rows = await cursor.fetchall()
            return [_row_to_rule(row) for row in rows]


async def get_rule(name: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM rules WHERE name = ?", (name,)) as cursor:
            row = await cursor.fetchone()
            return _row_to_rule(row) if row else None


async def upsert_rule(rule: dict) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO rules (name, description, device, condition, severity, cooldown, actions, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rule["name"],
            rule.get("description", ""),
            rule.get("device", "*"),
            json.dumps(rule.get("condition", {})),
            rule.get("severity", "info"),
            rule.get("cooldown", 300),
            json.dumps(rule.get("actions", [])),
            1 if rule.get("active", True) else 0,
            rule.get("created_at", time.time()),
        ))
        await db.commit()


async def delete_rule(name: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM rules WHERE name = ?", (name,))
        await db.commit()
        return cursor.rowcount > 0


async def toggle_rule(name: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE rules SET active = CASE WHEN active = 1 THEN 0 ELSE 1 END WHERE name = ?",
            (name,)
        )
        await db.commit()
    return await get_rule(name)


# --- Alerts ---

async def add_alert(rule_name: str, device_id: str, severity: str,
                    message: str, value: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO alerts (rule_name, device_id, severity, message, value, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (rule_name, device_id, severity, message, value, time.time()))
        await db.commit()


async def get_alerts(severity: str | None = None, limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if severity:
            query = "SELECT * FROM alerts WHERE severity = ? ORDER BY created_at DESC LIMIT ?"
            params = (severity, limit)
        else:
            query = "SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?"
            params = (limit,)
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


def _row_to_rule(row) -> dict:
    return {
        "name": row["name"],
        "description": row["description"],
        "device": row["device"],
        "condition": json.loads(row["condition"]),
        "severity": row["severity"],
        "cooldown": row["cooldown"],
        "actions": json.loads(row["actions"]),
        "active": bool(row["active"]),
        "created_at": row["created_at"],
    }
