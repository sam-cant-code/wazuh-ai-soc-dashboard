"""
Alert Processing Pipeline
Transforms raw Wazuh alerts into normalized Alert objects
Handles normalization, validation, enrichment, and error tolerance
"""

from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime, timezone
import hashlib
import json
import logging

from app.models import Alert, Agent, Rule, MITREInfo, AlertData

logger = logging.getLogger(__name__)


# =====================================================================
# NORMALIZATION & VALIDATION
# =====================================================================

class AlertNormalizer:
    """Normalizes field names for consistency"""

    FIELD_MAPPINGS = {
        "source_ip": "srcip",
        "src_ip": "srcip",
        "destination_ip": "dstip",
        "dest_ip": "dstip",
    }

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        normalized = raw.copy()
        for old, new in self.FIELD_MAPPINGS.items():
            if old in normalized:
                normalized[new] = normalized.pop(old)
        return normalized


class AlertValidator:
    """Validates alert integrity"""

    @staticmethod
    def validate(alert: Alert) -> Tuple[bool, Optional[str]]:
        if not alert.id:
            return False, "Missing alert ID"
        if not alert.timestamp:
            return False, "Missing timestamp"
        if not alert.agent or not alert.agent.id:
            return False, "Missing agent information"
        if not alert.rule or not alert.rule.id:
            return False, "Missing rule information"
        if not 0 <= alert.rule.level <= 15:
            return False, f"Invalid severity level: {alert.rule.level}"
        return True, None


# =====================================================================
# PROCESSOR
# =====================================================================

class AlertProcessor:
    """
    Converts raw Wazuh alerts into normalized Alert objects.

    Design goals:
    - Fault tolerant
    - Deterministic IDs
    - Extensible enrichment pipeline
    """

    def __init__(self):
        self.normalizer = AlertNormalizer()
        self.validators = [AlertValidator.validate]
        self.enrichers: List[Callable[[Dict[str, Any], Alert], Alert]] = []

    # -----------------------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------------------

    def add_enricher(self, enricher: Callable[[Dict[str, Any], Alert], Alert]):
        self.enrichers.append(enricher)
        logger.info(f"Registered enricher: {enricher.__name__}")

    def process(self, raw_alert: Dict[str, Any]) -> Optional[Alert]:
        try:
            raw = self.normalizer.normalize(raw_alert)

            alert = Alert(
                id=self._generate_alert_id(raw),
                timestamp=self._parse_timestamp(raw.get("timestamp")),
                agent=self._parse_agent(raw.get("agent", {})),
                rule=self._parse_rule(raw.get("rule", {})),
                data=self._parse_data(raw.get("data")),
                location=raw.get("location"),
                full_log=raw.get("full_log"),
                decoder=raw.get("decoder"),
            )

            # Enrichment pipeline
            for enricher in self.enrichers:
                try:
                    alert = enricher(raw, alert)
                except Exception as e:
                    logger.warning(f"Enricher {enricher.__name__} failed: {e}")

            # Validation
            for validator in self.validators:
                valid, error = validator(alert)
                if not valid:
                    logger.warning(f"Invalid alert dropped: {error}")
                    return None

            return alert

        except Exception:
            logger.exception("Failed to process alert")
            return None

    def process_batch(self, raw_alerts: List[Dict[str, Any]]) -> List[Alert]:
        alerts = []
        for raw in raw_alerts:
            alert = self.process(raw)
            if alert:
                alerts.append(alert)
        return alerts

    # -----------------------------------------------------------------
    # INTERNAL HELPERS
    # -----------------------------------------------------------------

    def _generate_alert_id(self, raw: Dict[str, Any]) -> str:
        """
        Deterministic, non-cryptographic ID.
        Stable across reloads for identical alerts.
        """
        content = json.dumps(raw, sort_keys=True, default=str)
        digest = hashlib.md5(content.encode()).hexdigest()[:10]  # not for security
        ts = raw.get("timestamp", "").replace(":", "").replace("-", "")
        return f"{ts}_{digest}"

    def _parse_timestamp(self, ts: Optional[str]) -> datetime:
        if not ts:
            return datetime.utcnow()

        try:
            ts = ts.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(ts)
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            logger.warning(f"Invalid timestamp '{ts}', using current time")
            return datetime.utcnow()

    def _parse_agent(self, data: Dict[str, Any]) -> Agent:
        return Agent(
            id=data.get("id", "unknown"),
            name=data.get("name", "unknown"),
            ip=data.get("ip"),
        )

    def _parse_rule(self, data: Dict[str, Any]) -> Rule:
        mitre = None
        if "mitre" in data:
            m = data["mitre"]
            mitre = MITREInfo(
                id=m.get("id", []),
                tactic=m.get("tactic", []),
                technique=m.get("technique", []),
            )

        return Rule(
            id=data.get("id", "unknown"),
            level=int(data.get("level", 0)),
            description=data.get("description", ""),
            groups=data.get("groups", []),
            mitre=mitre,
            firedtimes=data.get("firedtimes"),
        )

    def _parse_data(self, data: Optional[Dict[str, Any]]) -> Optional[AlertData]:
        if not data:
            return None

        win = data.get("win", {})
        return AlertData(
            srcip=data.get("srcip"),
            srcport=data.get("srcport"),
            dstip=data.get("dstip"),
            dstport=data.get("dstport"),
            dstuser=data.get("dstuser"),
            srcuser=data.get("srcuser"),
            process_name=data.get("process_name"),
            process_id=data.get("process_id"),
            win_eventdata=win.get("eventdata"),
            win_system=win.get("system"),
            extra=data,
        )
