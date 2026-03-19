#!/bin/bash
export $(grep -v '^\#' /opt/planeagent/apps/api/.env | xargs)
cd /opt/planeagent/apps/api
source venv/bin/activate
exec python manage.py runserver 0.0.0.0:8000
