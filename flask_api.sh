source backend/venv/bin/activate
nohup gunicorn --chdir backend --bind 0.0.0.0:5000 app:app \
  --worker-class gevent --workers 2 --access-logfile - > log.txt 2>&1 &

# python3 backend/app.py
