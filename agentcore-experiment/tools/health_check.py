"""
System health check tool for monitoring and status reporting
"""

from typing import Dict, Any
from datetime import datetime
import random
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from common import observability, ObservabilityLevel


async def system_health_check() -> Dict[str, Any]:
    """
    Perform a system health check
    Demonstrates monitoring and status reporting
    """
    trace_id = observability.start_trace("system_health_check")
    observability.add_span(trace_id, "health_check_start")
    
    try:
        # Simulate various system checks
        checks = {
            "mcp_server": "healthy",
            "memory_usage": random.randint(20, 80),
            "cpu_usage": random.randint(10, 60),
            "active_traces": len(observability.traces),
            "total_metrics": sum(len(v) for v in observability.metrics.values()),
            "uptime_seconds": random.randint(1000, 100000),
            "last_error": None,
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
        
        # Determine overall health
        if checks["memory_usage"] > 90 or checks["cpu_usage"] > 90:
            health_status = "degraded"
        else:
            health_status = "healthy"
        
        observability.add_span(trace_id, "health_check_complete", checks)
        observability.record_metric("health_checks", 1, tags={"status": health_status})
        
        observability.end_trace(trace_id)
        observability.log(ObservabilityLevel.INFO, f"Health check completed: {health_status}")
        
        return {
            "status": health_status,
            "checks": checks,
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat(),
            "observability_summary": {
                "total_traces": len(observability.traces),
                "total_metrics": sum(len(v) for v in observability.metrics.values()),
                "recent_traces": observability.get_recent_traces()
            }
        }
        
    except Exception as e:
        observability.end_trace(trace_id, "error", str(e))
        observability.log(ObservabilityLevel.ERROR, f"Health check failed: {str(e)}")
        raise