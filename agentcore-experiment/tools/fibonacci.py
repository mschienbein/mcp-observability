"""
Fibonacci calculation tool with performance tracking
"""

from typing import Dict, Any
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from common import observability, ObservabilityLevel


async def calculate_fibonacci(n: int) -> Dict[str, Any]:
    """
    Calculate the nth Fibonacci number
    Demonstrates computational tool with performance tracking
    """
    trace_id = observability.start_trace("calculate_fibonacci")
    observability.add_span(trace_id, "input_validation", {"n": n})
    
    try:
        if n < 0:
            raise ValueError("Fibonacci number must be non-negative")
        if n > 100:
            raise ValueError("Maximum n is 100 to prevent overflow")
        
        observability.add_span(trace_id, "computation_start")
        
        # Calculate Fibonacci
        if n <= 1:
            result = n
        else:
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            result = b
        
        observability.add_span(trace_id, "computation_complete", {"result": result})
        observability.record_metric("fibonacci_calculations", 1)
        observability.record_metric("fibonacci_max_n", n, tags={"type": "input"})
        
        observability.end_trace(trace_id)
        
        return {
            "n": n,
            "fibonacci": result,
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        observability.end_trace(trace_id, "error", str(e))
        observability.log(ObservabilityLevel.ERROR, f"Fibonacci calculation failed: {str(e)}")
        raise