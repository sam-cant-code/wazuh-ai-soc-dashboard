"""
Alert Service - Business logic for alert processing and querying
Handles alert parsing, filtering, aggregation, and metric calculation
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
import logging

from app.models import (
    Alert, FilterParams, SeverityLevel, TimelineDataPoint
)
from app.services.cache_service import CacheService
from app.alert_parser import AlertParser
from app.alert_processor import AlertProcessor

logger = logging.getLogger(__name__)


class AlertService:
    """
    Core service for alert management
    Provides methods for loading, filtering, and analyzing alerts
    """

    def __init__(self, alerts_file: str, cache_service: CacheService):
        self.alerts_file = Path(alerts_file)
        self.cache = cache_service
        self.parser = AlertParser(str(alerts_file))
        self.processor = AlertProcessor()

        # Indexes
        self._agent_index: Dict[str, List[str]] = defaultdict(list)
        self._rule_index: Dict[str, List[str]] = defaultdict(list)
        self._time_index: List[Tuple[datetime, str]] = []

        logger.info(f"AlertService initialized with file: {self.alerts_file}")

    # =====================================================================
    # LOADING
    # =====================================================================

    async def load_recent_alerts(self, hours: int = 24) -> int:
        """
        Load recent alerts from file into cache and rebuild indexes
        """
        logger.info(f"Loading alerts from last {hours} hours...")

        # IMPORTANT: clear state before reload
        self._agent_index.clear()
        self._rule_index.clear()
        self._time_index.clear()
        self.cache.clear()

        start_time = datetime.utcnow() - timedelta(hours=hours)
        loaded = 0
        failed = 0

        try:
            for raw_alert in self.parser.parse_alerts(
                start_time=start_time,
                reverse=True
            ):
                alert = self.processor.process(raw_alert)
                if not alert:
                    failed += 1
                    continue

                self.cache.put(alert.id, alert)
                self._update_indexes(alert)
                loaded += 1

            self._time_index.sort(key=lambda x: x[0])

            logger.info(
                f"Loaded {loaded} alerts (failed: {failed}) | "
                f"Cache size: {self.cache.size()}"
            )
            return loaded

        except FileNotFoundError:
            logger.error(f"Alerts file not found: {self.alerts_file}")
            return 0
        except Exception:
            logger.exception("Error loading alerts")
            raise

    def _update_indexes(self, alert: Alert):
        self._agent_index[alert.agent.id].append(alert.id)
        self._rule_index[alert.rule.id].append(alert.id)
        self._time_index.append((alert.timestamp, alert.id))

    # =====================================================================
    # RETRIEVAL
    # =====================================================================

    async def get_alerts(
        self,
        limit: int,
        offset: int,
        filters: Optional[FilterParams] = None
    ) -> Tuple[List[Alert], int]:

        alert_ids = self._get_filtered_ids(filters)
        total = len(alert_ids)

        paginated = alert_ids[offset: offset + limit]
        alerts = [self.cache.get(aid) for aid in paginated if self.cache.get(aid)]

        return alerts, total

    async def get_alert_by_id(self, alert_id: str) -> Optional[Alert]:
        return self.cache.get(alert_id)

    async def search_alerts(
        self,
        query: str,
        fields: List[str],
        filters: Optional[FilterParams],
        limit: int,
        offset: int
    ) -> Tuple[List[Alert], int]:

        query = query.lower()
        matched = []

        for _, alert_id in reversed(self._time_index):
            alert = self.cache.get(alert_id)
            if not alert:
                continue

            if self._matches_query(alert, query, fields):
                matched.append(alert_id)

        if filters:
            matched = [
                aid for aid in matched
                if self._matches_filters(self.cache.get(aid), filters)
            ]

        total = len(matched)
        paginated = matched[offset: offset + limit]
        alerts = [self.cache.get(aid) for aid in paginated if self.cache.get(aid)]

        return alerts, total

    # =====================================================================
    # FILTERING
    # =====================================================================

    def _get_filtered_ids(self, filters: Optional[FilterParams]) -> List[str]:
        """
        Use indexes where possible, fallback to full scan
        """
        if not filters:
            return [aid for _, aid in reversed(self._time_index)]

        candidate_ids: Optional[set] = None

        if filters.agent_id:
            candidate_ids = set(self._agent_index.get(filters.agent_id, []))

        if filters.rule_id:
            rule_ids = set(self._rule_index.get(filters.rule_id, []))
            candidate_ids = rule_ids if candidate_ids is None else candidate_ids & rule_ids

        if candidate_ids is None:
            candidate_ids = {aid for _, aid in self._time_index}

        # Final pass for non-indexed filters
        results = []
        for aid in sorted(
            candidate_ids,
            key=lambda x: self.cache.get(x).timestamp if self.cache.get(x) else datetime.min,
            reverse=True
        ):
            alert = self.cache.get(aid)
            if alert and self._matches_filters(alert, filters):
                results.append(aid)

        return results

    def _matches_filters(self, alert: Alert, filters: FilterParams) -> bool:
        if filters.severity_min is not None and alert.rule.level < filters.severity_min:
            return False
        if filters.severity_max is not None and alert.rule.level > filters.severity_max:
            return False

        if filters.agent_id and alert.agent.id != filters.agent_id:
            return False
        if filters.agent_name and alert.agent.name != filters.agent_name:
            return False

        if filters.rule_id and alert.rule.id != filters.rule_id:
            return False
        if filters.rule_group and filters.rule_group not in (alert.rule.groups or []):
            return False

        if filters.mitre_technique:
            if not alert.rule.mitre or filters.mitre_technique not in alert.rule.mitre.id:
                return False

        if filters.start_time and alert.timestamp < filters.start_time:
            return False
        if filters.end_time and alert.timestamp > filters.end_time:
            return False

        return True

    # =====================================================================
    # SEARCH HELPERS
    # =====================================================================

    def _matches_query(self, alert: Alert, query: str, fields: List[str]) -> bool:
        for field in fields:
            value = self._get_nested_field(alert, field)
            if value and query in str(value).lower():
                return True
        return False

    def _get_nested_field(self, obj: Any, path: str) -> Any:
        current = obj
        for part in path.split("."):
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    # =====================================================================
    # METRICS
    # =====================================================================

    async def get_severity_distribution(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, int]:

        result = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for _, aid in self._time_index:
            alert = self.cache.get(aid)
            if not alert:
                continue

            if start_time and alert.timestamp < start_time:
                continue
            if end_time and alert.timestamp > end_time:
                continue

            severity = SeverityLevel.from_rule_level(alert.rule.level)
            result[severity.value] += 1

        return result

    async def get_agent_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:

        counts = Counter()
        info = {}

        for _, aid in self._time_index:
            alert = self.cache.get(aid)
            if not alert:
                continue

            if start_time and alert.timestamp < start_time:
                continue
            if end_time and alert.timestamp > end_time:
                continue

            counts[alert.agent.id] += 1
            info[alert.agent.id] = {
                "name": alert.agent.name,
                "ip": alert.agent.ip
            }

        return [
            {
                "agent_id": aid,
                "agent_name": info[aid]["name"],
                "agent_ip": info[aid]["ip"],
                "alert_count": count
            }
            for aid, count in counts.most_common(top_n)
        ]

    async def get_timeline_data(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        interval: str
    ) -> List[TimelineDataPoint]:

        interval_map = {
            "1m": 1, "5m": 5, "15m": 15,
            "1h": 60, "6h": 360, "1d": 1440
        }
        bucket = timedelta(minutes=interval_map.get(interval, 60))

        if not self._time_index:
            return []

        start_time = start_time or self._time_index[0][0]
        end_time = end_time or self._time_index[-1][0]

        buckets = defaultdict(lambda: {
            "total": 0,
            "severity": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            "rules": Counter()
        })

        for _, aid in self._time_index:
            alert = self.cache.get(aid)
            if not alert:
                continue

            if alert.timestamp < start_time or alert.timestamp > end_time:
                continue

            bucket_time = alert.timestamp - (alert.timestamp - start_time) % bucket
            buckets[bucket_time]["total"] += 1
            sev = SeverityLevel.from_rule_level(alert.rule.level)
            buckets[bucket_time]["severity"][sev.value] += 1
            buckets[bucket_time]["rules"][alert.rule.id] += 1

        timeline = []
        for ts in sorted(buckets):
            b = buckets[ts]
            timeline.append(TimelineDataPoint(
                timestamp=ts,
                total_alerts=b["total"],
                severity_breakdown=b["severity"],
                top_rules=[
                    {"rule_id": r, "count": c}
                    for r, c in b["rules"].most_common(3)
                ]
            ))

        return timeline
