#!/usr/bin/env bash
# ABUTAHUNT — Production Deploy Script
# Prepared by Abuta (@abuta_art)
set -euo pipefail

# ── CONFIG ────────────────────────────────────────────────────────────────────
PROJECT="abutahunt"
COMPOSE="docker-compose"

# ── CHECKS ────────────────────────────────────────────────────────────────────
echo "🔍 Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || COMPOSE="docker compose"
[ -f ".env" ] || { echo "❌ .env file missing. Copy .env.example and fill in secrets."; exit 1; }

# ── BUILD ─────────────────────────────────────────────────────────────────────
echo "🔨 Building images..."
$COMPOSE build --no-cache

# ── START ─────────────────────────────────────────────────────────────────────
echo "🚀 Starting services..."
$COMPOSE up -d

# ── WAIT FOR DB ───────────────────────────────────────────────────────────────
echo "⏳ Waiting for PostgreSQL..."
sleep 8

# ── SEED DATA ─────────────────────────────────────────────────────────────────
echo "🌱 Seeding initial data..."
$COMPOSE exec bot python migrations/init_data.py || echo "⚠️  Seed may have already run (OK)"

# ── STATUS ────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ABUTAHUNT is running!"
echo ""
$COMPOSE ps
echo ""
echo "📋 Useful commands:"
echo "  Logs:    $COMPOSE logs -f bot"
echo "  Stop:    $COMPOSE down"
echo "  Restart: $COMPOSE restart bot"
echo "  DB:      $COMPOSE exec db psql -U abutahunt abutahunt"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
