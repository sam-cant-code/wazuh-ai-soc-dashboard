"""
NDJSON Alert Parser
Streaming parser for Wazuh alerts.json
"""

import json
from typing import Iterator, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


class AlertParser:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._validate_file()

    def _validate_file(self) -> None:
        if not self.file_path.exists():
            raise FileNotFoundError(f"Alerts file not found: {self.file_path}")
        if not self.file_path.is_file():
            raise ValueError(f"Path is not a file: {self.file_path}")

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def parse_alerts(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_alerts: Optional[int] = None,
        reverse: bool = False
    ) -> Iterator[Dict[str, Any]]:

        if reverse:
            yield from self._parse_reverse(start_time, end_time, max_alerts)
            return

        yielded = 0

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    alert = json.loads(line)
                except json.JSONDecodeError:
                    logger.debug(f"Malformed JSON at line {line_no}")
                    continue

                if not self._passes_time_filter(alert, start_time, end_time):
                    continue

                yield alert
                yielded += 1

                if max_alerts and yielded >= max_alerts:
                    break

    # ------------------------------------------------------------------
    # REVERSE PARSING
    # ------------------------------------------------------------------

    def _parse_reverse(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        max_alerts: Optional[int]
    ) -> Iterator[Dict[str, Any]]:

        yielded = 0
        buffer = b""

        with open(self.file_path, "rb") as f:
            f.seek(0, 2)
            position = f.tell()

            while position > 0:
                chunk_size = min(8192, position)
                position -= chunk_size
                f.seek(position)
                buffer = f.read(chunk_size) + buffer

                lines = buffer.split(b"\n")
                buffer = lines[0]

                for raw in reversed(lines[1:]):
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue

                    try:
                        alert = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    alert_time = self._extract_timestamp(alert)

                    # Early exit: alerts are getting older
                    if start_time and alert_time and alert_time < start_time:
                        return

                    if not self._passes_time_filter(alert, start_time, end_time):
                        continue

                    yield alert
                    yielded += 1

                    if max_alerts and yielded >= max_alerts:
                        return

    # ------------------------------------------------------------------
    # TIME HANDLING
    # ------------------------------------------------------------------

    def _passes_time_filter(
        self,
        alert: Dict[str, Any],
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> bool:

        if not start_time and not end_time:
            return True

        alert_time = self._extract_timestamp(alert)
        if not alert_time:
            return True

        if start_time and alert_time < start_time:
            return False
        if end_time and alert_time > end_time:
            return False

        return True

    def _extract_timestamp(self, alert: Dict[str, Any]) -> Optional[datetime]:
        ts = alert.get("timestamp")
        if not ts:
            return None

        try:
            ts = ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts)
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # UTILITIES
    # ------------------------------------------------------------------

    def count_alerts(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        return sum(1 for _ in self.parse_alerts(start_time, end_time))

    def get_file_info(self) -> Dict[str, Any]:
        stat = self.file_path.stat()
        return {
            "path": str(self.file_path),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
