#!/usr/bin/env bash
set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║      Red HMS – Automated Setup       ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Virtual environment
if [ ! -d "venv" ]; then
    echo "→ Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "→ Virtual environment active."

# Dependencies
echo "→ Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "→ Dependencies installed."

# Migrations
echo "→ Running migrations..."
python manage.py makemigrations accounts rooms guests billing reports --no-input 2>/dev/null || true
python manage.py migrate --no-input
echo "→ Database ready."

# Static files
echo "→ Collecting static files..."
python manage.py collectstatic --no-input -v 0
echo "→ Static files ready."

echo ""
echo "══════════════════════════════════════════"
echo "  ✅  Setup complete!"
echo ""
echo "  Next steps:"
echo "    python manage.py createsuperuser"
echo "    python manage.py runserver"
echo ""
echo "  Site  → http://127.0.0.1:8000/"
echo "  Admin → http://127.0.0.1:8000/admin/"
echo "══════════════════════════════════════════"
