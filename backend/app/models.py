# app/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_rule_level(cls, level: int):
        if level < 5: return cls.LOW
        if level < 10: return cls.MEDIUM
        if level < 13: return cls.HIGH
        return cls.CRITICAL

class Agent(BaseModel):
    id: str
    name: str
    ip: Optional[str] = None

class MITREInfo(BaseModel):
    id: List[str] = []
    tactic: List[str] = []
    technique: List[str] = []

class Rule(BaseModel):
    id: str
    level: int
    description: str
    groups: List[str] = []
    mitre: Optional[MITREInfo] = None
    firedtimes: Optional[int] = None

class AlertData(BaseModel):
    srcip: Optional[str] = None
    srcport: Optional[str] = None
    dstip: Optional[str] = None
    dstport: Optional[str] = None
    dstuser: Optional[str] = None
    srcuser: Optional[str] = None
    process_name: Optional[str] = None
    process_id: Optional[str] = None
    win_eventdata: Optional[Dict[str, Any]] = None
    win_system: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None

class Alert(BaseModel):
    id: str
    timestamp: datetime
    agent: Agent
    rule: Rule
    data: Optional[AlertData] = None
    location: Optional[str] = None
    full_log: Optional[str] = None
    decoder: Optional[Dict[str, Any]] = None

# API Request/Response Models
class FilterParams(BaseModel):
    severity_min: Optional[int] = None
    severity_max: Optional[int] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    rule_id: Optional[str] = None
    rule_group: Optional[str] = None
    mitre_technique: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class AlertListResponse(BaseModel):
    alerts: List[Alert]
    total: int
    limit: int
    offset: int

class MetricResponse(BaseModel):
    metric_name: str
    data: Any
    timestamp: datetime

class TimelineDataPoint(BaseModel):
    timestamp: datetime
    total_alerts: int
    severity_breakdown: Dict[str, int]
    top_rules: List[Dict[str, Any]]
class AlertResponse(Alert):
    pass