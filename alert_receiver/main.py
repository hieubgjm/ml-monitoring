"""A small Alertmanager webhook receiver with optional generic webhook forwarding."""

from __future__ import annotations

import json
import logging
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.request import Request, urlopen


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "").strip()
MAX_PAYLOAD_BYTES = 1_000_000


class AlertReceiverHandler(BaseHTTPRequestHandler):
    """Accept Alertmanager webhooks and optionally relay their original payload."""

    server_version = "MLMonitoringAlertReceiver/1.0"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler convention
        if self.path == "/health":
            self._send_response(HTTPStatus.OK, {"status": "healthy"})
            return
        self._send_response(HTTPStatus.NOT_FOUND, {"detail": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler convention
        if self.path != "/alerts":
            self._send_response(HTTPStatus.NOT_FOUND, {"detail": "not found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0 or content_length > MAX_PAYLOAD_BYTES:
            self._send_response(HTTPStatus.BAD_REQUEST, {"detail": "invalid payload size"})
            return

        payload = self.rfile.read(content_length)
        try:
            alert_group = json.loads(payload)
        except json.JSONDecodeError:
            self._send_response(HTTPStatus.BAD_REQUEST, {"detail": "invalid JSON"})
            return

        alerts = alert_group.get("alerts", [])
        logger.warning(
            "Received Alertmanager group status=%s alerts=%d",
            alert_group.get("status", "unknown"),
            len(alerts),
        )
        for alert in alerts:
            labels = alert.get("labels", {})
            logger.warning(
                "alert=%s severity=%s dag=%s task=%s status=%s",
                labels.get("alertname", "unknown"),
                labels.get("severity", "unknown"),
                labels.get("dag_id", "n/a"),
                labels.get("task_id", "n/a"),
                alert.get("status", "unknown"),
            )

        self._forward_if_configured(payload)
        self._send_response(HTTPStatus.OK, {"status": "received"})

    def _forward_if_configured(self, payload: bytes) -> None:
        if not ALERT_WEBHOOK_URL:
            return

        request = Request(
            ALERT_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                logger.info("Forwarded alert payload with HTTP %s", response.status)
        except URLError:
            logger.exception("Could not forward alert payload to configured webhook")

    def _send_response(self, status: HTTPStatus, body: dict[str, str]) -> None:
        encoded_body = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded_body)))
        self.end_headers()
        self.wfile.write(encoded_body)

    def log_message(self, format: str, *args: object) -> None:
        logger.info("%s - %s", self.address_string(), format % args)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8085), AlertReceiverHandler)
    logger.info("Alert receiver is listening on port 8085")
    server.serve_forever()
