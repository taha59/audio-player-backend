source backend/venv/bin/activate
nohup gunicorn --chdir backend --bind 0.0.0.0:5000 app:app > log.txt 2>&1 &
