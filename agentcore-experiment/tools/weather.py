"""
Weather simulation tool for testing external API patterns
"""

from typing import Dict, Any
from datetime import datetime, timedelta
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from common import observability, ObservabilityLevel


async def weather_simulator(
    location: str = "New York",
    days_ahead: int = 0
) -> Dict[str, Any]:
    """
    Simulate weather data for testing
    Demonstrates external API simulation with caching consideration
    """
    trace_id = observability.start_trace("weather_simulator")
    observability.add_span(trace_id, "request_received", {
        "location": location,
        "days_ahead": days_ahead
    })
    
    try:
        if days_ahead < 0 or days_ahead > 7:
            raise ValueError("Days ahead must be between 0 and 7")
        
        observability.add_span(trace_id, "simulating_weather")
        
        # Simulate weather data
        base_temp = random.randint(50, 90)
        weather_conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Foggy"]
        
        weather = {
            "location": location,
            "date": (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d"),
            "temperature": {
                "high": base_temp + random.randint(0, 10),
                "low": base_temp - random.randint(0, 10),
                "current": base_temp,
                "unit": "fahrenheit"
            },
            "condition": random.choice(weather_conditions),
            "humidity": random.randint(30, 90),
            "wind_speed": random.randint(0, 30),
            "precipitation_chance": random.randint(0, 100),
            "uv_index": random.randint(1, 11)
        }
        
        observability.add_span(trace_id, "weather_generated", weather)
        observability.record_metric("weather_requests", 1, tags={"location": location})
        
        observability.end_trace(trace_id)
        observability.log(ObservabilityLevel.INFO, f"Weather simulated for {location}")
        
        return {
            "weather": weather,
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat(),
            "cached": False  # In production, this would check cache
        }
        
    except Exception as e:
        observability.end_trace(trace_id, "error", str(e))
        observability.log(ObservabilityLevel.ERROR, f"Weather simulation failed: {str(e)}")
        raise