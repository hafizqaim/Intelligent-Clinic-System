"""Idempotently ensures one bootstrap clinic exists, so a fresh deployment
(with no shell access, e.g. Render's free tier) always has a clinic_id to
register the first user against, without any manual database access.

Safe to run on every startup: uses a fixed UUID and ON CONFLICT DO NOTHING.
"""

import asyncio

from sqlalchemy import text

from app.database import SessionLocal

BOOTSTRAP_CLINIC_ID = "00000000-0000-0000-0000-000000000001"


async def main() -> None:
    async with SessionLocal() as db:
        await db.execute(
            text(
                """
                INSERT INTO clinics (id, name, address, phone_number, created_at)
                VALUES (CAST(:id AS uuid), :name, :addr, :phone, now())
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": BOOTSTRAP_CLINIC_ID,
                "name": "Demo Clinic",
                "addr": "1 Bootstrap Way",
                "phone": "+1-555-0100",
            },
        )
        await db.commit()
    print(f"bootstrap clinic ready: {BOOTSTRAP_CLINIC_ID}")


if __name__ == "__main__":
    asyncio.run(main())
