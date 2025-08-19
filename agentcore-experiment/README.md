# AgentCore MCP Experiment with Enhanced Observability

An MCP server deployment for AWS Bedrock AgentCore Runtime featuring OpenTelemetry integration and CloudWatch GenAI Observability.

## 🚀 New: Enhanced Observability Features

Based on AWS AgentCore observability best practices, this experiment now includes:

### OpenTelemetry Integration
- **Distributed Tracing**: Full OpenTelemetry trace propagation
- **Span Management**: Automatic span creation with context managers
- **Metrics Collection**: Counters, histograms, and custom metrics
- **OTLP Export**: Send telemetry to any OTLP-compatible backend
- **AWS Lambda Instrumentation**: Auto-instrumentation when running in Lambda

### CloudWatch GenAI Observability
- **Custom Metrics**: Tool execution duration, error rates, invocation counts
- **Structured Logs**: JSON-formatted logs with trace context
- **Transaction Search**: Query and filter transactions by attributes
- **Log Groups**: Automatic creation and management
- **Real-time Monitoring**: Live metrics and logs in CloudWatch console

### Transaction Search Capability
- Search transactions by tool name, session ID, or status
- Filter by time range and duration
- Correlate traces across distributed systems
- Export telemetry data for analysis

## Project Structure

```
agentcore-experiment/
├── common/
│   ├── observability.py         # Basic observability (no dependencies)
│   └── observability_enhanced.py # Enhanced with OpenTelemetry + CloudWatch
├── tools/
│   ├── fibonacci.py             # Standard implementation
│   ├── fibonacci_enhanced.py    # With enhanced observability
│   ├── text_analyzer.py
│   ├── data_generator.py
│   ├── weather.py
│   └── health_check.py
├── mcps/
│   └── experiment_server/
│       └── server.py            # FastMCP server
├── deployment/
│   └── deploy_experiment.py    # AgentCore deployment
├── tests/
│   └── test_deployed_server.py
├── .env.example                 # Configuration template
└── requirements.txt             # Including OpenTelemetry deps
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Core Configuration
MCP_SERVICE_NAME=agentcore-mcp-experiment
ENVIRONMENT=development

# OpenTelemetry (optional but recommended)
ENABLE_OTEL=true
OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317

# CloudWatch Integration
ENABLE_CLOUDWATCH=true
CLOUDWATCH_NAMESPACE=AgentCore/MCP
AWS_REGION=us-east-1
```

## Enhanced Tool Example

The `fibonacci_enhanced.py` demonstrates the new observability pattern:

```python
# Context manager for automatic tracing
with observability.trace_tool("calculate_fibonacci", session_id) as span:
    # OpenTelemetry attributes
    if span:
        span.set_attribute("fibonacci.input", n)
    
    # Add custom spans
    observability.add_span(trace_id, "computation", {"algorithm": "iterative"})
    
    # Record metrics to CloudWatch
    observability.record_metric("fibonacci_calculations", 1)
```

## Deployment with Observability

### Prerequisites

Install dependencies including OpenTelemetry:

```bash
uv pip install -r requirements.txt
```

### Deploy to AgentCore

```bash
python deployment/deploy_experiment.py
```

The deployment automatically:
1. Configures CloudWatch log groups
2. Sets up metric namespaces
3. Enables transaction search
4. Creates monitoring dashboards

### Monitor in CloudWatch

After deployment, view your observability data:

1. **CloudWatch Logs**
   - Navigate to `/aws/agentcore/agentcore-mcp-experiment`
   - Filter by trace_id or transaction_id
   - Use CloudWatch Insights for queries

2. **CloudWatch Metrics**
   - Namespace: `AgentCore/MCP`
   - Metrics: `ToolExecutionDuration`, `tool_invocations`, `tool_errors`
   - Create custom dashboards

3. **Transaction Search**
   - Use the `search_transactions()` API
   - Filter by tool, session, status, or custom attributes
   - Export results for analysis

## Observability Patterns

### 1. Distributed Tracing
Every tool invocation creates a trace with:
- Unique trace ID for correlation
- Transaction ID for search
- Spans for execution stages
- Duration and status tracking

### 2. Metrics Collection
Automatic metrics for:
- Tool invocation counts
- Execution duration (p50, p95, p99)
- Error rates by tool and error type
- Custom business metrics

### 3. Structured Logging
JSON logs with:
- Trace and span context
- Session and user IDs
- Tool parameters and results
- Error details with stack traces

### 4. Health Monitoring
The `system_health_check` tool provides:
- Recent trace summaries
- Metrics aggregation
- System status
- Telemetry export

## OpenTelemetry Setup (Optional)

For full OpenTelemetry support, run a collector:

```bash
# Using Docker
docker run -p 4317:4317 -p 4318:4318 \
  otel/opentelemetry-collector-contrib:latest
```

Or use AWS Distro for OpenTelemetry:

```bash
# Install ADOT Collector
aws cloudformation create-stack \
  --stack-name adot-collector \
  --template-url https://aws-otel.github.io/...
```

## Testing Observability

### Local Testing with Traces

```python
# Test with session tracking
python -c "
from mcps.experiment_server import mcp
import asyncio

async def test():
    result = await mcp.tools['calculate_fibonacci'](
        n=10, 
        session_id='test-session-123'
    )
    print(f'Trace ID: {result['trace_id']}')
    print(f'Transaction ID: {result['transaction_id']}')

asyncio.run(test())
"
```

### Query Transactions

```python
# Search for specific transactions
from common.observability_enhanced import observability

# Find all fibonacci calculations
results = observability.search_transactions({
    'tool_name': 'calculate_fibonacci',
    'status': 'success'
})

# Export all telemetry
telemetry = observability.export_telemetry()
```

## CloudWatch Dashboards

Create a custom dashboard for your MCP server:

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AgentCore/MCP", "ToolExecutionDuration", {"stat": "Average"}],
          [".", ".", {"stat": "p99"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Tool Performance"
      }
    }
  ]
}
```

## Best Practices

1. **Use Context Managers**: Leverage `trace_tool()` for automatic span management
2. **Add Meaningful Attributes**: Include business context in spans
3. **Record Custom Metrics**: Track domain-specific KPIs
4. **Structure Logs**: Use consistent JSON format for queries
5. **Monitor Costs**: Set up CloudWatch alarms for usage

## Troubleshooting Observability

### Missing Traces
- Verify `ENABLE_OTEL=true` in environment
- Check OTLP endpoint connectivity
- Look for errors in CloudWatch Logs

### No CloudWatch Metrics
- Confirm IAM permissions for `cloudwatch:PutMetricData`
- Check `ENABLE_CLOUDWATCH=true`
- Verify AWS credentials

### Transaction Search Not Working
- Ensure traces complete with `end_trace()`
- Check transaction_data population
- Verify search query syntax

## Cost Optimization

- **Sampling**: Implement trace sampling for high-volume tools
- **Retention**: Set appropriate log retention periods
- **Metrics**: Use metric filters instead of custom metrics where possible
- **Alarms**: Set up cost alarms for CloudWatch usage

## References

- [AWS AgentCore Observability Tutorial](https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/01-tutorials/06-AgentCore-observability)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [CloudWatch GenAI Observability](https://docs.aws.amazon.com/cloudwatch/latest/monitoring/CloudWatch-GenAI.html)
- [AWS Distro for OpenTelemetry](https://aws-otel.github.io/docs/)

---

This enhanced implementation follows AWS best practices for AgentCore observability, providing production-ready monitoring and debugging capabilities.