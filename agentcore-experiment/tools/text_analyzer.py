"""
Text analysis tool with detailed metrics
"""

from typing import Dict, Any
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from common import observability, ObservabilityLevel


async def analyze_text(text: str) -> Dict[str, Any]:
    """
    Analyze text and return statistics
    Demonstrates text processing with detailed metrics
    """
    trace_id = observability.start_trace("analyze_text")
    observability.add_span(trace_id, "text_received", {"length": len(text)})
    
    try:
        # Basic text analysis
        words = text.split()
        sentences = text.split('.')
        
        observability.add_span(trace_id, "analysis_start")
        
        analysis = {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
            "unique_words": len(set(words)),
            "longest_word": max(words, key=len) if words else "",
            "text_complexity": "simple" if len(words) < 50 else "moderate" if len(words) < 200 else "complex"
        }
        
        observability.add_span(trace_id, "analysis_complete", analysis)
        observability.record_metric("text_analyzed_chars", len(text), unit="characters")
        observability.record_metric("text_analyzed_words", len(words), unit="words")
        
        observability.end_trace(trace_id)
        
        return {
            "analysis": analysis,
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        observability.end_trace(trace_id, "error", str(e))
        observability.log(ObservabilityLevel.ERROR, f"Text analysis failed: {str(e)}")
        raise