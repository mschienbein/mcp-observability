#!/usr/bin/env python3
"""
Comprehensive Langfuse SDK test
Tests the Langfuse Python SDK connection and basic operations
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
def load_env():
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        print(f"✓ Loaded environment from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")
        print("   Using environment variables")

def test_langfuse_connection():
    """Test Langfuse connection and basic operations"""
    
    # Check required environment variables
    required_vars = ['LANGFUSE_SECRET_KEY', 'LANGFUSE_PUBLIC_KEY', 'LANGFUSE_HOST']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("\nPlease set these in your .env file or environment:")
        for var in missing:
            print(f"  export {var}=<value>")
        return False
    
    try:
        from langfuse import Langfuse
    except ImportError:
        print("❌ Langfuse not installed. Run: pip install langfuse")
        return False
    
    # Initialize Langfuse client
    try:
        langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_HOST")
        )
        print(f"✅ Langfuse client initialized")
        print(f"   Host: {os.getenv('LANGFUSE_HOST')}")
        print(f"   Project: {os.getenv('LANGFUSE_PUBLIC_KEY').split('-')[-1]}")
    except Exception as e:
        print(f"❌ Failed to initialize Langfuse: {e}")
        return False
    
    # Test trace creation
    try:
        print("\n📊 Testing trace creation...")
        trace = langfuse.trace(
            name="test-trace",
            user_id="test-user",
            session_id="test-session",
            metadata={"test": True, "timestamp": datetime.now().isoformat()},
            tags=["test", "sdk-test"],
            input={"query": "test input"},
            output={"response": "test output"}
        )
        print(f"✅ Trace created with ID: {trace.id}")
        
        # Add a generation
        generation = trace.generation(
            name="test-generation",
            model="gpt-3.5-turbo",
            input=[{"role": "user", "content": "Test"}],
            output={"role": "assistant", "content": "Test response"},
            metadata={"test": True}
        )
        print(f"✅ Generation added with ID: {generation.id}")
        
        # Add a score
        trace.score(
            name="test-score",
            value=1.0,
            comment="Test successful"
        )
        print("✅ Score added to trace")
        
        # Flush events
        langfuse.flush()
        print("✅ Events flushed to Langfuse")
        
        print(f"\n🔗 View trace at:")
        print(f"   {os.getenv('LANGFUSE_HOST')}/project/{os.getenv('LANGFUSE_PUBLIC_KEY').split('-')[-1]}/traces/{trace.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            langfuse.shutdown()
            print("\n✅ Langfuse client shutdown complete")
        except:
            pass

def main():
    """Run the test"""
    print("=" * 60)
    print("🚀 Langfuse SDK Test")
    print("=" * 60)
    
    # Load environment
    load_env()
    
    # Run test
    success = test_langfuse_connection()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()