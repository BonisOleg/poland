#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python -m pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py load_initial_data
python manage.py ensure_superuser
