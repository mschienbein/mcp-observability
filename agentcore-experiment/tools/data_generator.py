"""
Random data generation tool for testing
"""

from typing import Dict, Any, List, Union
from datetime import datetime
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from common import observability, ObservabilityLevel


async def generate_random_data(
    data_type: str = "numbers",
    count: int = 10,
    min_value: int = 1,
    max_value: int = 100
) -> Dict[str, Any]:
    """
    Generate random test data
    Demonstrates data generation with parameter validation
    """
    trace_id = observability.start_trace("generate_random_data")
    observability.add_span(trace_id, "parameter_validation", {
        "data_type": data_type,
        "count": count,
        "min_value": min_value,
        "max_value": max_value
    })
    
    try:
        if count < 1 or count > 1000:
            raise ValueError("Count must be between 1 and 1000")
        
        observability.add_span(trace_id, "generation_start")
        
        data: List[Union[int, float, bool, str]]
        
        if data_type == "numbers":
            data = [random.randint(min_value, max_value) for _ in range(count)]
        elif data_type == "floats":
            data = [random.uniform(min_value, max_value) for _ in range(count)]
        elif data_type == "booleans":
            data = [random.choice([True, False]) for _ in range(count)]
        elif data_type == "strings":
            words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]
            data = [random.choice(words) for _ in range(count)]
        else:
            raise ValueError(f"Unknown data type: {data_type}")
        
        observability.add_span(trace_id, "generation_complete", {"items_generated": len(data)})
        observability.record_metric("random_data_generated", count, tags={"type": data_type})
        
        observability.end_trace(trace_id)
        
        metadata = {
            "type": data_type,
            "count": len(data)
        }
        
        if data_type in ["numbers", "floats"]:
            metadata["min"] = min(data)  # type: ignore
            metadata["max"] = max(data)  # type: ignore
        
        return {
            "data": data,
            "metadata": metadata,
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        observability.end_trace(trace_id, "error", str(e))
        observability.log(ObservabilityLevel.ERROR, f"Data generation failed: {str(e)}")
        raise