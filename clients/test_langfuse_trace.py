#!/usr/bin/env python3
"""Langfuse trace test - creates a complete trace with spans and events"""

import os
import sys
import time
import uuid
from pathlib import Path
from datetime import datetime

# Load .env
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

from langfuse import Langfuse
try:
    from langfuse.decorators import observe, langfuse_context
    HAS_DECORATORS = True
except ImportError:
    # Older version or different API
    HAS_DECORATORS = False
    observe = lambda: lambda f: f  # No-op decorator
    class FakeLangfuseContext:
        def update_current_trace(self, **kwargs): pass
        def update_current_observation(self, **kwargs): pass
        def score_current_trace(self, **kwargs): pass
        def score_current_observation(self, **kwargs): pass
    langfuse_context = FakeLangfuseContext()

# Initialize client
langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)

print("✅ Langfuse client initialized")
print(f"   Host: {os.getenv('LANGFUSE_HOST')}")
print("")

# Test 1: Using decorators for automatic tracing
@observe()
def process_data(data: str) -> str:
    """Simulated data processing function"""
    time.sleep(0.1)  # Simulate processing
    return f"Processed: {data}"

@observe()
def generate_response(prompt: str) -> str:
    """Simulated LLM call"""
    langfuse_context.update_current_observation(
        metadata={"model": "gpt-3.5-turbo", "temperature": 0.7},
        input=prompt,
        model="gpt-3.5-turbo",
        usage={"input": 10, "output": 20, "total": 30}
    )
    
    # Process the prompt
    result = process_data(prompt)
    
    # Simulate response generation
    time.sleep(0.2)
    response = f"Response to '{result}'"
    
    # Score the generation
    langfuse_context.score_current_observation(
        name="quality",
        value=0.95,
        comment="High quality response"
    )
    
    return response

@observe()
def main_workflow():
    """Main traced workflow"""
    print("📊 Test 1: Creating traced workflow with decorators...")
    
    # Update trace metadata
    langfuse_context.update_current_trace(
        name="test-workflow-trace",
        session_id=f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        user_id="test-user-123",
        metadata={
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "environment": "test"
        },
        tags=["test", "trace", "demo"],
        release="v1.0.0",
        version="1.0.0"
    )
    
    # Execute the workflow
    prompt = "What is the capital of France?"
    response = generate_response(prompt)
    
    print(f"   Input: {prompt}")
    print(f"   Output: {response}")
    
    # Score the entire trace
    langfuse_context.score_current_trace(
        name="overall_quality",
        value=1.0,
        comment="Successful test execution"
    )
    
    return response

# Test 2: Manual span/event creation
def test_manual_trace():
    """Test creating spans and events manually"""
    print("\n📊 Test 2: Creating manual trace with spans and events...")
    
    # Trace ID must be 32 lowercase hex characters
    trace_id = uuid.uuid4().hex  # This gives us exactly 32 hex chars
    
    # Create an event (simplest trace element)
    event = langfuse.create_event(
        trace_context={"trace_id": trace_id},
        name="data-loaded",
        metadata={"source": "test", "records": 100},
        level="DEFAULT",
        status_message="Data loaded successfully"
    )
    print(f"   ✓ Created event: data-loaded")
    
    # Create another event with more details
    event2 = langfuse.create_event(
        trace_context={"trace_id": trace_id},
        name="processing-complete",
        input={"data": "test input"},
        output={"result": "processed data"},
        metadata={"processor": "v2", "duration_ms": 100},
        level="DEFAULT",
        status_message="Processing complete"
    )
    print(f"   ✓ Created event: processing-complete")
    
    # Simulate some work
    time.sleep(0.2)
    
    # Add a score to the trace
    langfuse.create_score(
        trace_id=trace_id,
        name="manual-test-score",
        value=0.9,
        comment="Manual trace test successful"
    )
    print("   ✓ Added score to trace")
    
    return trace_id

try:
    # Run Test 1: Decorator-based tracing
    result = main_workflow()
    trace_id_1 = langfuse.get_current_trace_id()
    print(f"   ✓ Workflow completed")
    if trace_id_1:
        print(f"   Trace ID: {trace_id_1}")
    
    # Run Test 2: Manual trace creation
    trace_id_2 = test_manual_trace()
    print(f"   Trace ID: {trace_id_2}")
    
    # Flush all data
    print("\n💾 Flushing all traces to Langfuse...")
    langfuse.flush()
    time.sleep(2)  # Give it time to send
    
    print("\n✅ All trace tests completed successfully!")
    print("\n🔗 View your traces in Langfuse:")
    print(f"   {os.getenv('LANGFUSE_HOST')}/project/cmegfhksf0006mn06q79d8eab/traces")
    
    if trace_id_1:
        trace_url_1 = langfuse.get_trace_url(trace_id=trace_id_1)
        if trace_url_1:
            print(f"\n   Workflow trace: {trace_url_1}")
    
    trace_url_2 = langfuse.get_trace_url(trace_id=trace_id_2)
    if trace_url_2:
        print(f"   Manual trace: {trace_url_2}")
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    langfuse.shutdown()
    print("\n✅ Client shutdown complete")