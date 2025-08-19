"""
AgentCore Observability Middleware with Optional OpenTelemetry and CloudWatch
Provides distributed tracing, metrics, and structured logging for MCP tools
Compatible with AWS CloudWatch GenAI Observability
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json
import random
import os
import time
from contextlib import contextmanager

# Optional OpenTelemetry imports (graceful fallback if not available)
try:
    from opentelemetry import trace, metrics
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.instrumentation.aws_lambda import AwsLambdaInstrumentor
    # Use non-deprecated imports for semantic conventions
    try:
        from opentelemetry.semconv.attributes import (
            SERVICE_NAME,
            SERVICE_VERSION,
            DEPLOYMENT_ENVIRONMENT_NAME
        )
    except ImportError:
        # Fallback to string literals if new imports not available
        SERVICE_NAME = "service.name"
        SERVICE_VERSION = "service.version"
        DEPLOYMENT_ENVIRONMENT_NAME = "deployment.environment"
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    print("OpenTelemetry not available, using basic observability")

# Optional CloudWatch integration
try:
    import boto3
    from botocore.exceptions import ClientError
    CLOUDWATCH_AVAILABLE = True
except ImportError:
    CLOUDWATCH_AVAILABLE = False
    print("CloudWatch integration not available")


class ObservabilityLevel(Enum):
    """Logging levels for observability"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AgentCoreObservability:
    """
    Observability middleware for AgentCore with optional OpenTelemetry and CloudWatch
    Provides production-ready tracing, metrics, and logging with graceful fallback
    """
    
    def __init__(self, 
                 service_name: str = "agentcore-mcp-experiment",
                 enable_otel: bool = True,
                 enable_cloudwatch: bool = True,
                 cloudwatch_namespace: str = "AgentCore/MCP",
                 otlp_endpoint: Optional[str] = None):
        """
        Initialize observability with optional enhancements
        
        Args:
            service_name: Name of the service for tracing
            enable_otel: Enable OpenTelemetry integration if available
            enable_cloudwatch: Enable CloudWatch metrics if available
            cloudwatch_namespace: CloudWatch metrics namespace
            otlp_endpoint: OTLP collector endpoint (defaults to env var)
        """
        self.service_name = service_name
        self.traces: List[Dict[str, Any]] = []
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self.session_data: Dict[str, Any] = {}
        self.transaction_data: Dict[str, Any] = {}  # For transaction search
        
        # Initialize OpenTelemetry if available and enabled
        self.tracer = None
        self.meter = None
        self.tool_invocation_counter = None
        self.tool_duration_histogram = None
        self.error_counter = None
        
        if OTEL_AVAILABLE and enable_otel:
            self._init_opentelemetry(otlp_endpoint)
        
        # Initialize CloudWatch if available and enabled
        self.cloudwatch = None
        self.cloudwatch_logs = None
        self.cloudwatch_namespace = cloudwatch_namespace
        self.log_stream = None
        
        if CLOUDWATCH_AVAILABLE and enable_cloudwatch:
            self._init_cloudwatch(cloudwatch_namespace)
    
    def _init_opentelemetry(self, otlp_endpoint: Optional[str] = None):
        """Initialize OpenTelemetry tracing and metrics"""
        try:
            # Create resource with service information using non-deprecated attributes
            resource_attributes = {
                "agentcore.runtime": "true",
                "mcp.server": "experiment"
            }
            
            # Add standard attributes with proper keys
            if OTEL_AVAILABLE:
                resource_attributes[SERVICE_NAME] = self.service_name
                resource_attributes[SERVICE_VERSION] = "1.0.0"
                resource_attributes[DEPLOYMENT_ENVIRONMENT_NAME] = os.getenv("ENVIRONMENT", "development")
            
            resource = Resource.create(resource_attributes)
            
            # Setup tracing
            trace.set_tracer_provider(TracerProvider(resource=resource))
            tracer_provider = trace.get_tracer_provider()
            
            # Configure OTLP exporter
            endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
            span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__, "1.0.0")
            
            # Setup metrics
            metrics.set_meter_provider(MeterProvider(resource=resource))
            self.meter = metrics.get_meter(__name__, "1.0.0")
            
            # Create common metrics
            self.tool_invocation_counter = self.meter.create_counter(
                "tool_invocations",
                description="Number of tool invocations",
                unit="1"
            )
            
            self.tool_duration_histogram = self.meter.create_histogram(
                "tool_duration",
                description="Tool execution duration",
                unit="ms"
            )
            
            self.error_counter = self.meter.create_counter(
                "tool_errors",
                description="Number of tool errors",
                unit="1"
            )
            
            # Instrument AWS Lambda if running in Lambda
            if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
                AwsLambdaInstrumentor().instrument()
                
        except Exception as e:
            print(f"OpenTelemetry initialization failed: {e}")
            self.tracer = None
            self.meter = None
    
    def _init_cloudwatch(self, namespace: str):
        """Initialize CloudWatch client"""
        try:
            self.cloudwatch = boto3.client('cloudwatch')
            self.cloudwatch_namespace = namespace
            self.cloudwatch_logs = boto3.client('logs')
            
            # Create log group if it doesn't exist
            log_group = f"/aws/agentcore/{self.service_name}"
            try:
                self.cloudwatch_logs.create_log_group(logGroupName=log_group)
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                    raise
            
            # Create log stream
            self.log_stream = f"{self.service_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            try:
                self.cloudwatch_logs.create_log_stream(
                    logGroupName=log_group,
                    logStreamName=self.log_stream
                )
            except ClientError:
                pass  # Stream might already exist
                
        except Exception as e:
            print(f"CloudWatch initialization failed: {e}")
            self.cloudwatch = None
            self.cloudwatch_logs = None
    
    @contextmanager
    def trace_tool(self, tool_name: str, session_id: Optional[str] = None):
        """
        Context manager for tracing tool execution with OpenTelemetry
        
        Usage:
            with observability.trace_tool("my_tool", session_id) as span:
                # Tool implementation
                if span:
                    span.set_attribute("custom.attribute", value)
        """
        # Start local trace
        trace_id = self.start_trace(tool_name, session_id)
        
        # Start OpenTelemetry span if available
        span = None
        if self.tracer:
            span = self.tracer.start_span(
                tool_name,
                attributes={
                    "tool.name": tool_name,
                    "session.id": session_id or "unknown",
                    "trace.id": trace_id
                }
            )
            
        start_time = time.time()
        
        try:
            yield span
            
            # Record success metrics
            duration_ms = (time.time() - start_time) * 1000
            self.end_trace(trace_id, "success")
            
            if self.tool_invocation_counter:
                self.tool_invocation_counter.add(1, {"tool": tool_name, "status": "success"})
            if self.tool_duration_histogram:
                self.tool_duration_histogram.record(duration_ms, {"tool": tool_name})
            
            if span:
                span.set_status(Status(StatusCode.OK))
                
        except Exception as e:
            # Record error metrics
            self.end_trace(trace_id, "error", str(e))
            
            if self.error_counter:
                self.error_counter.add(1, {"tool": tool_name, "error": type(e).__name__})
            
            if span:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
            
            raise
            
        finally:
            if span:
                span.end()
    
    def start_trace(self, tool_name: str, session_id: Optional[str] = None) -> str:
        """Start a new trace for a tool invocation"""
        trace_id = f"trace_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"
        
        trace = {
            "trace_id": trace_id,
            "tool_name": tool_name,
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "status": "started",
            "spans": [],
            "transaction_id": f"txn_{trace_id}"  # For transaction search
        }
        
        self.traces.append(trace)
        
        # Store for transaction search
        self.transaction_data[trace["transaction_id"]] = {
            "trace_id": trace_id,
            "tool_name": tool_name,
            "session_id": session_id,
            "start_time": trace["start_time"]
        }
        
        return trace_id
    
    def add_span(self, trace_id: str, span_name: str, attributes: Dict[str, Any] = None):
        """Add a span to an existing trace"""
        for trace in self.traces:
            if trace["trace_id"] == trace_id:
                span = {
                    "span_id": f"span_{datetime.now().timestamp()}",
                    "name": span_name,
                    "timestamp": datetime.now().isoformat(),
                    "attributes": attributes or {}
                }
                trace["spans"].append(span)
                
                # Create OpenTelemetry span if available
                if self.tracer:
                    with self.tracer.start_as_current_span(span_name) as otel_span:
                        for key, value in (attributes or {}).items():
                            otel_span.set_attribute(f"span.{key}", str(value))
                
                break
    
    def end_trace(self, trace_id: str, status: str = "success", error: Optional[str] = None):
        """End a trace and calculate duration"""
        for trace in self.traces:
            if trace["trace_id"] == trace_id:
                trace["end_time"] = datetime.now().isoformat()
                trace["status"] = status
                if error:
                    trace["error"] = error
                
                # Calculate duration
                start = datetime.fromisoformat(trace["start_time"])
                end = datetime.fromisoformat(trace["end_time"])
                trace["duration_ms"] = (end - start).total_seconds() * 1000
                
                # Update transaction data
                if trace["transaction_id"] in self.transaction_data:
                    self.transaction_data[trace["transaction_id"]].update({
                        "end_time": trace["end_time"],
                        "duration_ms": trace["duration_ms"],
                        "status": status,
                        "error": error
                    })
                
                # Send to CloudWatch if available
                self._send_to_cloudwatch(trace)
                
                break
    
    def _send_to_cloudwatch(self, trace: Dict[str, Any]):
        """Send trace data to CloudWatch"""
        if not self.cloudwatch:
            return
        
        try:
            # Send custom metric
            self.cloudwatch.put_metric_data(
                Namespace=self.cloudwatch_namespace,
                MetricData=[
                    {
                        'MetricName': 'ToolExecutionDuration',
                        'Value': trace.get('duration_ms', 0),
                        'Unit': 'Milliseconds',
                        'Dimensions': [
                            {'Name': 'ToolName', 'Value': trace['tool_name']},
                            {'Name': 'Status', 'Value': trace['status']}
                        ],
                        'Timestamp': datetime.now()
                    }
                ]
            )
            
            # Send structured log
            if self.cloudwatch_logs and self.log_stream:
                log_event = {
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'message': json.dumps({
                        'type': 'trace',
                        'trace_id': trace['trace_id'],
                        'transaction_id': trace.get('transaction_id'),
                        'tool_name': trace['tool_name'],
                        'session_id': trace.get('session_id'),
                        'duration_ms': trace.get('duration_ms'),
                        'status': trace['status'],
                        'error': trace.get('error'),
                        'spans_count': len(trace['spans'])
                    })
                }
                
                self.cloudwatch_logs.put_log_events(
                    logGroupName=f"/aws/agentcore/{self.service_name}",
                    logStreamName=self.log_stream,
                    logEvents=[log_event]
                )
            
        except Exception as e:
            print(f"Failed to send to CloudWatch: {e}")
    
    def record_metric(self, name: str, value: float, unit: str = "count", tags: Dict[str, str] = None):
        """Record a metric with CloudWatch support"""
        metric_key = f"{name}_{datetime.now().strftime('%Y%m%d')}"
        if metric_key not in self.metrics:
            self.metrics[metric_key] = []
        
        self.metrics[metric_key].append({
            "timestamp": datetime.now().isoformat(),
            "value": value,
            "unit": unit,
            "tags": tags or {}
        })
        
        # Send to CloudWatch
        if self.cloudwatch:
            try:
                dimensions = [{'Name': k, 'Value': v} for k, v in (tags or {}).items()]
                self.cloudwatch.put_metric_data(
                    Namespace=self.cloudwatch_namespace,
                    MetricData=[{
                        'MetricName': name,
                        'Value': value,
                        'Unit': unit.capitalize(),
                        'Dimensions': dimensions,
                        'Timestamp': datetime.now()
                    }]
                )
            except Exception as e:
                print(f"Failed to send metric to CloudWatch: {e}")
    
    def log(self, level: ObservabilityLevel, message: str, context: Dict[str, Any] = None):
        """Log a message with context and CloudWatch support"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "message": message,
            "context": context or {},
            "service": self.service_name
        }
        
        # Print locally
        print(json.dumps(log_entry))
        
        # Send to CloudWatch Logs
        if self.cloudwatch_logs and self.log_stream:
            try:
                self.cloudwatch_logs.put_log_events(
                    logGroupName=f"/aws/agentcore/{self.service_name}",
                    logStreamName=self.log_stream,
                    logEvents=[{
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'message': json.dumps(log_entry)
                    }]
                )
            except Exception as e:
                print(f"Failed to send log to CloudWatch: {e}")
        
        return log_entry
    
    def search_transactions(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for transactions based on criteria
        Enables transaction search feature mentioned in AWS docs
        """
        results = []
        
        for txn_id, txn_data in self.transaction_data.items():
            match = True
            
            # Check each query criterion
            for key, value in query.items():
                if key in txn_data:
                    if txn_data[key] != value:
                        match = False
                        break
            
            if match:
                results.append(txn_data)
        
        return results
    
    def get_recent_traces(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent traces with summary info"""
        recent = []
        for trace in self.traces[-limit:]:
            summary = {
                "tool": trace["tool_name"],
                "status": trace["status"],
                "duration_ms": trace.get("duration_ms", 0),
                "transaction_id": trace.get("transaction_id"),
                "spans_count": len(trace["spans"])
            }
            recent.append(summary)
        return recent
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics"""
        return {
            "total_metrics": sum(len(v) for v in self.metrics.values()),
            "metric_types": list(self.metrics.keys()),
            "service": self.service_name,
            "cloudwatch_enabled": self.cloudwatch is not None,
            "opentelemetry_enabled": self.tracer is not None
        }
    
    def export_telemetry(self) -> Dict[str, Any]:
        """Export all telemetry data for analysis"""
        return {
            "service": self.service_name,
            "traces": self.traces[-100:],  # Last 100 traces
            "metrics": self.metrics,
            "transactions": self.transaction_data,
            "summary": {
                "total_traces": len(self.traces),
                "total_transactions": len(self.transaction_data),
                "metrics_summary": self.get_metrics_summary()
            }
        }


# Global observability instance with graceful fallback
observability = AgentCoreObservability(
    service_name=os.getenv("MCP_SERVICE_NAME", "agentcore-mcp-experiment"),
    enable_otel=os.getenv("ENABLE_OTEL", "true").lower() == "true",
    enable_cloudwatch=os.getenv("ENABLE_CLOUDWATCH", "true").lower() == "true",
    cloudwatch_namespace=os.getenv("CLOUDWATCH_NAMESPACE", "AgentCore/MCP")
)