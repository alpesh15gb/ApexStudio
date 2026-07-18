#!/bin/bash
set -e

# Apex Studio — Initialization Script
# Run after first deployment to set up the platform

echo "=== Apex Studio Initialization ==="

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
until PGPASSWORD=${POSTGRES_PASSWORD:-apex} psql -h postgres -U ${POSTGRES_USER:-apex} -d ${POSTGRES_DB:-apex_studio} -c '\q' 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is ready."

# Run migrations
echo "Running database migrations..."
cd /app/backend
alembic upgrade head
echo "Migrations complete."

# Create default admin user (if not exists)
echo "Setting up default data..."
python -c "
from app.core.database import AsyncSessionLocal
from app.models.user import User
import asyncio

async def init():
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == 'admin@apexstudio.com'))
        if not result.scalar_one_or_none():
            from app.core.security import get_password_hash
            user = User(
                email='admin@apexstudio.com',
                password_hash=get_password_hash('admin123'),
                full_name='Admin',
                is_active=True,
                email_verified_at=__import__('datetime').datetime.utcnow()
            )
            session.add(user)
            await session.commit()
            print('Default admin user created (admin@apexstudio.com / admin123)')
        else:
            print('Admin user already exists')

asyncio.run(init())
"

echo "=== Initialization Complete ==="
