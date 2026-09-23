"""
Celery Beat entrypoint with a Prometheus liveness endpoint.
"""

import logging
import sys

from celery.apps.beat import Beat
from prometheus_client import start_http_server

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Keep the metrics endpoint in the same process as Beat so that
    # Prometheus reports the target as down when Beat exits.
    start_http_server(9102)

    logger.info("Starting Celery Beat with Prometheus metrics on port 9102")

    beat_instance = Beat(
        app=celery_app,
        loglevel="INFO",
    )
    beat_instance.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
