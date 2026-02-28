# Gunicorn configuration for the GRC Vendor Onboarding API
# Run with: gunicorn -c gunicorn.conf.py main:app

bind = "0.0.0.0:8000"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = "info"

# Graceful restart on SIGHUP
preload_app = False


def on_starting(server):
    """Run DB migrations once in the master process before workers fork."""
    from core.database import Base, engine
    Base.metadata.create_all(bind=engine)
