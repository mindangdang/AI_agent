from dataclasses import dataclass
from typing import Any

from psycopg.rows import dict_row


@dataclass(slots=True)
class TasteProfileRepository:
    conn: Any

    async def get_latest_summary(self, user_id: str) -> str | None:
        async with self.conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                "SELECT summary FROM taste_profile WHERE user_id = %s ORDER BY updated_at DESC LIMIT 1",
                (user_id,)
            )
            row = await cursor.fetchone()
            return row["summary"] if row else None

    async def upsert_summary(self, summary: str, user_id: str) -> None:
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO taste_profile (user_id, summary, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    summary = EXCLUDED.summary,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, summary)
            )
            await self.conn.commit()

    async def get_profile(self, user_id: str):
        async with self.conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute("SELECT * FROM taste_profile WHERE user_id = %s", (user_id,))
            row = await cursor.fetchone()
            return row if row else {"summary": ""}
