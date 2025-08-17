from aws_cdk import (
    Stack, Duration, aws_ec2 as ec2, aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns, CfnOutput
)
from constructs import Construct

class LangfuseStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc(self, "Vpc", max_azs=2, nat_gateways=1)
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        # --- Langfuse Web behind ALB
        web = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "LangfuseWeb",
            cluster=cluster,
            cpu=512, memory_limit_mib=2048, desired_count=2, public_load_balancer=True,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry("langfuse/langfuse:latest"),
                container_port=3000, enable_logging=True,
                environment={
                    "DATABASE_URL": "postgresql://USER:PASS@PG_HOST:5432/langfuse",
                    "CLICKHOUSE_URL": "https://ch-host:8443",
                    "CLICKHOUSE_USER": "default",
                    "CLICKHOUSE_PASSWORD": "CH_PASSWORD",
                    "CLICKHOUSE_DB": "default",
                    "CLICKHOUSE_MIGRATION_URL": "clickhouses://ch-host:9440/default?secure=true",
                    "REDIS_CONNECTION_STRING": "rediss://:REDIS_PASS@redis-host:6379",
                    "NEXTAUTH_SECRET": "GENERATE_ME",
                    "NEXTAUTH_URL": "https://obs.example.com",
                    "SALT": "CHANGE_ME",
                    "ENCRYPTION_KEY": "64_HEX_CHARS_CHANGE_ME",
                    "LANGFUSE_TRACING_ENVIRONMENT": "prod",
                    "NODE_OPTIONS": "--max-old-space-size=3072",
                },
            ),
            health_check_grace_period=Duration.seconds(60),
        )
        web.target_group.configure_health_check(path="/api/health", port="3000", healthy_http_codes="200")

        # --- Worker (no ALB)
        task_def = ecs.FargateTaskDefinition(self, "WorkerTaskDef", cpu=512, memory_limit_mib=2048)
        task_def.add_container(
            "Worker",
            image=ecs.ContainerImage.from_registry("langfuse/langfuse-worker:latest"),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="langfuse-worker"),
            environment={
                "DATABASE_URL": "postgresql://USER:PASS@PG_HOST:5432/langfuse",
                "CLICKHOUSE_URL": "https://ch-host:8443",
                "CLICKHOUSE_USER": "default",
                "CLICKHOUSE_PASSWORD": "CH_PASSWORD",
                "CLICKHOUSE_DB": "default",
                "CLICKHOUSE_MIGRATION_URL": "clickhouses://ch-host:9440/default?secure=true",
                "REDIS_CONNECTION_STRING": "rediss://:REDIS_PASS@redis-host:6379",
                "NEXTAUTH_SECRET": "GENERATE_ME",
                "SALT": "CHANGE_ME",
                "ENCRYPTION_KEY": "64_HEX_CHARS_CHANGE_ME",
                "LANGFUSE_TRACING_ENVIRONMENT": "prod",
                "NODE_OPTIONS": "--max-old-space-size=3072",
            },
        )
        ecs.FargateService(self, "LangfuseWorkerService", cluster=cluster, task_definition=task_def, desired_count=1,
                           assign_public_ip=False, vpc_subnets=ec2.SubnetSelection(
                               subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS))

        CfnOutput(self, "AlbUrl", value=f"http://{web.load_balancer.load_balancer_dns_name}")
