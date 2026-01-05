# backend/app/main.py
"""
Lightweight SIEM Dashboard - FastAPI Backend
Main application entry point with API routes and configuration
"""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
import logging

from app.models import (
    Alert, AlertResponse, AlertListResponse, 
    MetricResponse, TimelineDataPoint, FilterParams
)
from app.services.alert_service import AlertService
from app.services.cache_service import CacheService
from app.config import (
    load_config, 
    print_config, 
    get_uvicorn_log_level,
    should_expose_errors
)

# Load configuration FIRST (this also sets up logging)
try:
    config = load_config()
except Exception as e:
    print(f"FATAL: Failed to load configuration: {e}")
    raise

# Get logger AFTER logging is configured
logger = logging.getLogger(__name__)


# Application lifespan for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup/shutdown
    Initialize services and load initial data
    """
    logger.info("Starting SIEM Dashboard Backend...")
    print_config(config)
    
    # Initialize services with config values
    app.state.cache_service = CacheService(
        max_size=config["cache"]["max_size"]
    )
    
    app.state.alert_service = AlertService(
        alerts_file=config["alert_file"],
        cache_service=app.state.cache_service
    )
    
    # Load recent alerts into cache
    logger.info(f"Loading alerts from last {config['cache']['load_hours']} hours...")
    try:
        await app.state.alert_service.load_recent_alerts(
            hours=config["cache"]["load_hours"]
        )
        logger.info(f"Loaded {app.state.cache_service.size()} alerts")
    except FileNotFoundError:
        logger.warning(
            f"Alert file not found: {config['alert_file']}\n"
            "Run 'python generate_sample_alerts.py' to create sample data"
        )
    except Exception as e:
        logger.error(f"Error loading alerts: {e}")
    
    # Store config in app state for access in endpoints
    app.state.config = config
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down SIEM Dashboard Backend...")
    app.state.cache_service.clear()


# Initialize FastAPI app
app = FastAPI(
    title="Lightweight SIEM Dashboard API",
    description="REST API for Wazuh alert analysis and visualization",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if config.get("api", {}).get("enable_docs", True) else None
)


# CORS configuration from config.yaml
if config["cors"]["enabled"]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config["cors"]["origins"],
        allow_credentials=config["cors"]["allow_credentials"],
        allow_methods=config["cors"]["allow_methods"],
        allow_headers=config["cors"]["allow_headers"],
    )
    logger.info(f"CORS enabled for origins: {config['cors']['origins']}")


# Exception handler for consistent error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    Behavior changes based on configuration:
    - Development: Exposes full error details
    - Production: Hides implementation details
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Check if we should expose detailed errors
    expose_details = should_expose_errors(request.app.state.config)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if expose_details else "An error occurred. Check server logs."
        }
    )


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/api/v1/health")
async def health_check(request: Request):
    """
    Health check endpoint for monitoring
    Returns service status and basic statistics
    """
    cache_stats = request.app.state.cache_service.get_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "alert_file": request.app.state.config["alert_file"],
            "cache_size": request.app.state.config["cache"]["max_size"],
            "cache_hours": request.app.state.config["cache"]["load_hours"]
        },
        "cache": {
            "size": cache_stats["size"],
            "max_size": cache_stats["max_size"],
            "hit_rate": cache_stats["hit_rate"]
        }
    }


# ============================================================================
# ALERT ENDPOINTS
# ============================================================================

@app.get("/api/v1/alerts", response_model=AlertListResponse)
async def get_alerts(
    request: Request,
    limit: int = Query(
        default=None,  # Will use config default
        ge=1,
        le=None,  # Will use config max
        description="Maximum number of alerts to return"
    ),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    severity_min: Optional[int] = Query(None, ge=0, le=15, description="Minimum rule level"),
    severity_max: Optional[int] = Query(None, ge=0, le=15, description="Maximum rule level"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    rule_id: Optional[str] = Query(None, description="Filter by rule ID"),
    rule_group: Optional[str] = Query(None, description="Filter by rule group"),
    mitre_technique: Optional[str] = Query(None, description="Filter by MITRE technique ID"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO format)"),
):
    """
    Retrieve alerts with filtering and pagination
    
    Supports multiple filter criteria:
    - Severity range (rule level 0-15)
    - Agent identification (ID or name)
    - Rule matching (ID or group)
    - MITRE ATT&CK technique
    - Time range
    """
    try:
        # Apply config defaults if not specified
        if limit is None:
            limit = request.app.state.config.get("api", {}).get("default_page_size", 100)
        
        max_page_size = request.app.state.config.get("api", {}).get("max_page_size", 1000)
        if limit > max_page_size:
            limit = max_page_size
        
        service = request.app.state.alert_service
        
        # Build filter parameters
        filters = FilterParams(
            severity_min=severity_min,
            severity_max=severity_max,
            agent_id=agent_id,
            agent_name=agent_name,
            rule_id=rule_id,
            rule_group=rule_group,
            mitre_technique=mitre_technique,
            start_time=start_time,
            end_time=end_time
        )
        
        # Query alerts
        alerts, total = await service.get_alerts(
            limit=limit,
            offset=offset,
            filters=filters
        )
        
        return AlertListResponse(
            alerts=alerts,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/alerts/{alert_id}", response_model=Alert)
async def get_alert_by_id(request: Request, alert_id: str):
    """
    Retrieve a single alert by its unique ID
    """
    try:
        service = request.app.state.alert_service
        alert = await service.get_alert_by_id(alert_id)
        
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/alerts/search", response_model=AlertListResponse)
async def search_alerts(
    request: Request,
    search_params: Dict[str, Any],
    limit: int = Query(default=None, ge=1, le=None),
    offset: int = Query(0, ge=0)
):
    """
    Advanced alert search with complex query support
    
    Request body format:
    {
        "query": "failed authentication",
        "fields": ["rule.description", "data.dstuser"],
        "filters": {...}
    }
    """
    try:
        # Apply config defaults
        if limit is None:
            limit = request.app.state.config.get("api", {}).get("default_page_size", 100)
        
        max_page_size = request.app.state.config.get("api", {}).get("max_page_size", 1000)
        if limit > max_page_size:
            limit = max_page_size
        
        service = request.app.state.alert_service
        
        # Extract search parameters
        query = search_params.get("query", "")
        fields = search_params.get("fields", [])
        filters_dict = search_params.get("filters", {})
        
        # Convert filters dict to FilterParams
        filters = FilterParams(**filters_dict)
        
        # Perform search
        alerts, total = await service.search_alerts(
            query=query,
            fields=fields,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return AlertListResponse(
            alerts=alerts,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error searching alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# METRICS ENDPOINTS
# ============================================================================

@app.get("/api/v1/metrics/severity", response_model=MetricResponse)
async def get_severity_distribution(
    request: Request,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None)
):
    """
    Get distribution of alerts by severity level
    
    Returns count of alerts for each rule level (0-15)
    """
    try:
        service = request.app.state.alert_service
        distribution = await service.get_severity_distribution(start_time, end_time)
        
        return MetricResponse(
            metric_name="severity_distribution",
            data=distribution,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting severity distribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics/agents", response_model=MetricResponse)
async def get_agent_metrics(
    request: Request,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    top_n: int = Query(10, ge=1, le=100)
):
    """
    Get alert counts per agent
    
    Returns top N agents by alert volume
    """
    try:
        service = request.app.state.alert_service
        agent_metrics = await service.get_agent_metrics(start_time, end_time, top_n)
        
        return MetricResponse(
            metric_name="agent_metrics",
            data=agent_metrics,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting agent metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics/mitre", response_model=MetricResponse)
async def get_mitre_distribution(
    request: Request,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None)
):
    """
    Get distribution of MITRE ATT&CK techniques
    
    Returns count and percentage for each technique
    """
    try:
        service = request.app.state.alert_service
        mitre_dist = await service.get_mitre_distribution(start_time, end_time)
        
        return MetricResponse(
            metric_name="mitre_distribution",
            data=mitre_dist,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting MITRE distribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics/timeline", response_model=List[TimelineDataPoint])
async def get_timeline_data(
    request: Request,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    interval: str = Query(None, regex="^(1m|5m|15m|1h|6h|1d)$")
):
    """
    Get time-series alert data for timeline visualization
    
    Groups alerts by time interval (1m, 5m, 15m, 1h, 6h, 1d)
    Returns count per interval with severity breakdown
    """
    try:
        # Use config default if not specified
        if interval is None:
            interval = request.app.state.config.get("api", {}).get("default_timeline_interval", "1h")
        
        service = request.app.state.alert_service
        timeline = await service.get_timeline_data(start_time, end_time, interval)
        
        return timeline
        
    except Exception as e:
        logger.error(f"Error getting timeline data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AI EXTENSION ENDPOINTS (Placeholder for Future Implementation)
# ============================================================================

@app.post("/api/v1/ai/cluster")
async def cluster_alerts(request: Request, params: Dict[str, Any]):
    """
    Cluster related alerts into incidents
    
    Future implementation will use HDBSCAN or similar algorithm
    """
    return {
        "status": "not_implemented",
        "message": "Alert clustering module not yet implemented",
        "extension_point": "app.ai_modules.clustering.ClusteringModule"
    }


@app.get("/api/v1/ai/risk/{agent_id}")
async def get_risk_score(request: Request, agent_id: str):
    """
    Calculate dynamic risk score for an endpoint
    
    Future implementation will analyze alert patterns
    """
    return {
        "status": "not_implemented",
        "message": f"Risk scoring for agent {agent_id} not yet implemented",
        "extension_point": "app.ai_modules.risk_scoring.RiskScoringModule"
    }


@app.post("/api/v1/ai/summarize")
async def summarize_incident(request: Request, params: Dict[str, Any]):
    """
    Generate natural language summary of alert cluster
    
    Future implementation will use template-based or LLM summarization
    """
    return {
        "status": "not_implemented",
        "message": "Alert summarization module not yet implemented",
        "extension_point": "app.ai_modules.summarization.SummarizationModule"
    }


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.post("/api/v1/cache/refresh")
async def refresh_cache(request: Request):
    """
    Manually refresh the alert cache
    Useful for development or after manual alert file updates
    """
    try:
        service = request.app.state.alert_service
        hours = request.app.state.config["cache"]["load_hours"]
        await service.load_recent_alerts(hours=hours)
        
        cache_stats = request.app.state.cache_service.get_stats()
        
        return {
            "status": "success",
            "message": f"Cache refreshed with {cache_stats['size']} alerts",
            "cache_stats": cache_stats
        }
        
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/config")
async def get_config(request: Request):
    """
    Get current configuration (excluding sensitive data)
    Useful for debugging
    """
    cfg = request.app.state.config
    safe_config = {
        "alert_file": cfg["alert_file"],
        "cache": cfg["cache"],
        "server": {
            "host": cfg["server"]["host"],
            "port": cfg["server"]["port"],
            "workers": cfg["server"]["workers"],
            "reload": cfg["server"]["reload"]
        },
        "logging": {
            "level": cfg["logging"]["level"],
            "file": cfg["logging"].get("file")
        },
        "cors_enabled": cfg["cors"]["enabled"],
        "features": cfg.get("features", {}),
        "expose_error_details": should_expose_errors(cfg)
    }
    return safe_config


if __name__ == "__main__":
    import uvicorn
    
    # Get uvicorn settings from config
    uvicorn.run(
        "main:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        reload=config["server"]["reload"],
        workers=config["server"]["workers"],
        log_level=get_uvicorn_log_level(config)
    )