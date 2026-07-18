#!/bin/bash
# Health check script for Apex Studio services

SERVICE=${1:-all}

check_postgres() {
    PGPASSWORD=${POSTGRES_PASSWORD:-apex} psql -h localhost -U ${POSTGRES_USER:-apex} -d ${POSTGRES_DB:-apex_studio} -c '\q' 2>/dev/null
}

check_redis() {
    redis-cli ping > /dev/null 2>&1
}

check_backend() {
    curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1
}

case $SERVICE in
    postgres)
        check_postgres && echo "postgres: healthy" || echo "postgres: unhealthy"
        ;;
    redis)
        check_redis && echo "redis: healthy" || echo "redis: unhealthy"
        ;;
    backend)
        check_backend && echo "backend: healthy" || echo "backend: unhealthy"
        ;;
    all)
        echo "=== Apex Studio Health Check ==="
        check_postgres && echo "✓ postgres" || echo "✗ postgres"
        check_redis && echo "✓ redis" || echo "✗ redis"
        check_backend && echo "✓ backend" || echo "✗ backend"
        ;;
    *)
        echo "Usage: $0 {all|postgres|redis|backend}"
        exit 1
        ;;
esac
