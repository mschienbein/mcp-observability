import aws_cdk as cdk
from aws_cdk import (
    Stack,
    Duration,
    SecretValue,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_s3 as s3,
    aws_rds as rds,
    aws_elasticache as elasticache,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
)
from constructs import Construct


class LangfuseStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # --- Networking
        vpc = ec2.Vpc(self, "Vpc", max_azs=2, nat_gateways=1)
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        # Security groups
        rds_sg = ec2.SecurityGroup(self, "RdsSg", vpc=vpc, allow_all_outbound=True)
        redis_sg = ec2.SecurityGroup(self, "RedisSg", vpc=vpc, allow_all_outbound=True)

        # --- RDS PostgreSQL for Langfuse
        db_password_secret = secretsmanager.Secret(
            self,
            "LangfuseDbPassword",
            description="Password for the Langfuse PostgreSQL user",
            generate_secret_string=secretsmanager.SecretStringGenerator(exclude_punctuation=True, password_length=24),
        )

        db = rds.DatabaseInstance(
            self,
            "Postgres",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_15),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            multi_az=False,
            allocated_storage=20,
            credentials=rds.Credentials.from_password(
                username="langfuse",
                password=db_password_secret.secret_value,
            ),
            database_name="langfuse",
            security_groups=[rds_sg],
            deletion_protection=False,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Compose full DATABASE_URL as a secret so we can inject it as one variable
        db_url_secret = secretsmanager.Secret(
            self,
            "LangfuseDbUrl",
            description="DATABASE_URL for Langfuse",
            secret_string_value=SecretValue.unsafe_plain_text(
                cdk.Fn.join(
                    "",
                    [
                        "postgresql://langfuse:",
                        db_password_secret.secret_value.unsafe_unwrap(),
                        "@",
                        db.instance_endpoint.hostname,
                        ":",
                        cdk.Token.as_string(db.instance_endpoint.port),
                        "/langfuse",
                    ],
                )
            ),
        )

        # App secrets
        nextauth_secret = secretsmanager.Secret(
            self,
            "NextAuthSecret",
            description="NEXTAUTH_SECRET for Langfuse",
            generate_secret_string=secretsmanager.SecretStringGenerator(exclude_punctuation=True, password_length=32),
        )
        salt_secret = secretsmanager.Secret(
            self,
            "SaltSecret",
            description="SALT for Langfuse",
            generate_secret_string=secretsmanager.SecretStringGenerator(exclude_punctuation=True, password_length=32),
        )
        # ENCRYPTION_KEY must be 64 hex chars; use a static demo value (replace in prod)
        encryption_secret = secretsmanager.Secret(
            self,
            "EncryptionKeySecret",
            description="ENCRYPTION_KEY (64 hex) for Langfuse",
            secret_string_value=SecretValue.unsafe_plain_text(
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            ),
        )

        # --- ClickHouse (Langfuse v3) placeholders in Secrets Manager
        # Provide empty placeholders so you can fill values post-deploy.
        clickhouse_url_secret = secretsmanager.Secret(
            self,
            "ClickhouseUrl",
            description="CLICKHOUSE_URL for Langfuse v3 (e.g., https://<host>:8443/?ssl=true)",
            secret_string_value=SecretValue.unsafe_plain_text("TO_BE_SET"),
        )
        clickhouse_user_secret = secretsmanager.Secret(
            self,
            "ClickhouseUser",
            description="CLICKHOUSE_USER for Langfuse v3",
            secret_string_value=SecretValue.unsafe_plain_text("TO_BE_SET"),
        )
        clickhouse_password_secret = secretsmanager.Secret(
            self,
            "ClickhousePassword",
            description="CLICKHOUSE_PASSWORD for Langfuse v3",
            secret_string_value=SecretValue.unsafe_plain_text("TO_BE_SET"),
        )
        # Optional, used for migrations if different from CLICKHOUSE_URL
        clickhouse_migration_url_secret = secretsmanager.Secret(
            self,
            "ClickhouseMigrationUrl",
            description="CLICKHOUSE_MIGRATION_URL for Langfuse v3 (optional)",
            secret_string_value=SecretValue.unsafe_plain_text("TO_BE_SET"),
        )

        # Optional DB name (defaults to 'default')
        clickhouse_db_secret = secretsmanager.Secret(
            self,
            "ClickhouseDb",
            description="CLICKHOUSE_DB for Langfuse v3 (default: 'default')",
            secret_string_value=SecretValue.unsafe_plain_text("default"),
        )
        # Migration SSL toggle ("true" | "false"), not sensitive but stored for consistency
        clickhouse_migration_ssl_secret = secretsmanager.Secret(
            self,
            "ClickhouseMigrationSsl",
            description="CLICKHOUSE_MIGRATION_SSL for Langfuse v3 (\"true\" | \"false\")",
            secret_string_value=SecretValue.unsafe_plain_text("true"),
        )

        # --- ElastiCache Redis (single node) for Langfuse
        redis_subnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
        redis_subnet_group = elasticache.CfnSubnetGroup(
            self,
            "RedisSubnetGroup",
            description="Subnet group for Langfuse Redis",
            subnet_ids=[s.subnet_id for s in redis_subnets.subnets],
        )

        redis = elasticache.CfnCacheCluster(
            self,
            "Redis",
            engine="redis",
            cache_node_type="cache.t3.micro",
            num_cache_nodes=1,
            vpc_security_group_ids=[redis_sg.security_group_id],
            cache_subnet_group_name=redis_subnet_group.ref,
        )
        # Ensure subnet group is created before the cluster
        redis.add_dependency(redis_subnet_group)

        # --- S3 bucket for Langfuse v3 event uploads
        events_bucket = s3.Bucket(
            self,
            "EventsBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # --- Langfuse Web behind ALB
        web = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "LangfuseWeb",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=2048,
            desired_count=1,
            public_load_balancer=True,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry("langfuse/langfuse:latest"),
                container_port=3000,
                enable_logging=True,
                environment={
                    # Construct connection strings from provisioned resources
                    "REDIS_CONNECTION_STRING": f"redis://{redis.attr_redis_endpoint_address}:{redis.attr_redis_endpoint_port}",
                    # App config
                    "LANGFUSE_TRACING_ENVIRONMENT": "prod",
                    "NODE_OPTIONS": "--max-old-space-size=3072",
                    # Langfuse v3 S3 event uploads
                    "LANGFUSE_S3_EVENT_UPLOAD_BUCKET": events_bucket.bucket_name,
                    "LANGFUSE_S3_EVENT_UPLOAD_REGION": cdk.Aws.REGION,
                    "LANGFUSE_S3_EVENT_UPLOAD_PREFIX": "events/",
                    # Disable clustering unless you operate a ClickHouse cluster
                    "CLICKHOUSE_CLUSTER_ENABLED": "false",
                },
                secrets={
                    "DATABASE_URL": ecs.Secret.from_secrets_manager(db_url_secret),
                    "NEXTAUTH_SECRET": ecs.Secret.from_secrets_manager(nextauth_secret),
                    "SALT": ecs.Secret.from_secrets_manager(salt_secret),
                    "ENCRYPTION_KEY": ecs.Secret.from_secrets_manager(encryption_secret),
                    # ClickHouse (Langfuse v3)
                    "CLICKHOUSE_URL": ecs.Secret.from_secrets_manager(clickhouse_url_secret),
                    "CLICKHOUSE_USER": ecs.Secret.from_secrets_manager(clickhouse_user_secret),
                    "CLICKHOUSE_PASSWORD": ecs.Secret.from_secrets_manager(clickhouse_password_secret),
                    "CLICKHOUSE_MIGRATION_URL": ecs.Secret.from_secrets_manager(clickhouse_migration_url_secret),
                    "CLICKHOUSE_DB": ecs.Secret.from_secrets_manager(clickhouse_db_secret),
                    "CLICKHOUSE_MIGRATION_SSL": ecs.Secret.from_secrets_manager(clickhouse_migration_ssl_secret),
                },
            ),
            health_check_grace_period=Duration.seconds(60),
        )
        web.target_group.configure_health_check(path="/api/health", port="3000", healthy_http_codes="200")
        # Set NEXTAUTH_URL now that the load balancer is created
        if web.task_definition.default_container:
            web.task_definition.default_container.add_environment(
                "NEXTAUTH_URL",
                f"http://{web.load_balancer.load_balancer_dns_name}",
            )
        # Relax deployment requirements so stack creation doesn't wait on healthy tasks
        cfn_web_service = web.service.node.default_child
        if isinstance(cfn_web_service, ecs.CfnService):
            cfn_web_service.deployment_configuration = ecs.CfnService.DeploymentConfigurationProperty(
                minimum_healthy_percent=0,
                maximum_percent=200,
            )
        # Explicitly grant secret read permissions to the execution role used by ECS to fetch secrets
        if web.task_definition.execution_role:
            for _s in [
                db_url_secret,
                nextauth_secret,
                salt_secret,
                encryption_secret,
                clickhouse_url_secret,
                clickhouse_user_secret,
                clickhouse_password_secret,
                clickhouse_migration_url_secret,
                clickhouse_db_secret,
                clickhouse_migration_ssl_secret,
            ]:
                _s.grant_read(web.task_definition.execution_role)
        # Allow the web task to read/write to the events bucket (v3 event uploads)
        events_bucket.grant_read_write(web.task_definition.task_role)

        # Allow ECS tasks to reach RDS/Redis
        web_sg = web.service.connections.security_groups[0]
        rds_sg.add_ingress_rule(peer=web_sg, connection=ec2.Port.tcp(5432), description="Allow web to Postgres")
        redis_sg.add_ingress_rule(peer=web_sg, connection=ec2.Port.tcp(6379), description="Allow web to Redis")

        # --- Worker (no ALB)
        task_def = ecs.FargateTaskDefinition(self, "WorkerTaskDef", cpu=512, memory_limit_mib=2048)
        task_def.add_container(
            "Worker",
            image=ecs.ContainerImage.from_registry("langfuse/langfuse-worker:latest"),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="LangfuseWorker"),
            environment={
                "REDIS_CONNECTION_STRING": f"redis://{redis.attr_redis_endpoint_address}:{redis.attr_redis_endpoint_port}",
                "LANGFUSE_TRACING_ENVIRONMENT": "prod",
                "NODE_OPTIONS": "--max-old-space-size=3072",
                # Langfuse v3 S3 event uploads
                "LANGFUSE_S3_EVENT_UPLOAD_BUCKET": events_bucket.bucket_name,
                "LANGFUSE_S3_EVENT_UPLOAD_REGION": cdk.Aws.REGION,
                "LANGFUSE_S3_EVENT_UPLOAD_PREFIX": "events/",
                # Disable clustering unless you operate a ClickHouse cluster
                "CLICKHOUSE_CLUSTER_ENABLED": "false",
            },
            secrets={
                "DATABASE_URL": ecs.Secret.from_secrets_manager(db_url_secret),
                "NEXTAUTH_SECRET": ecs.Secret.from_secrets_manager(nextauth_secret),
                "SALT": ecs.Secret.from_secrets_manager(salt_secret),
                "ENCRYPTION_KEY": ecs.Secret.from_secrets_manager(encryption_secret),
                # ClickHouse (Langfuse v3)
                "CLICKHOUSE_URL": ecs.Secret.from_secrets_manager(clickhouse_url_secret),
                "CLICKHOUSE_USER": ecs.Secret.from_secrets_manager(clickhouse_user_secret),
                "CLICKHOUSE_PASSWORD": ecs.Secret.from_secrets_manager(clickhouse_password_secret),
                "CLICKHOUSE_MIGRATION_URL": ecs.Secret.from_secrets_manager(clickhouse_migration_url_secret),
                "CLICKHOUSE_DB": ecs.Secret.from_secrets_manager(clickhouse_db_secret),
                "CLICKHOUSE_MIGRATION_SSL": ecs.Secret.from_secrets_manager(clickhouse_migration_ssl_secret),
            },
        )
        worker = ecs.FargateService(
            self,
            "LangfuseWorkerService",
            cluster=cluster,
            task_definition=task_def,
            desired_count=0,
            assign_public_ip=False,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )
        # Relax deployment requirements for worker as well
        cfn_worker_service = worker.node.default_child
        if isinstance(cfn_worker_service, ecs.CfnService):
            cfn_worker_service.deployment_configuration = ecs.CfnService.DeploymentConfigurationProperty(
                minimum_healthy_percent=0,
                maximum_percent=200,
            )
        # Grant secret read permissions to the worker execution role
        if task_def.execution_role:
            for _s in [
                db_url_secret,
                nextauth_secret,
                salt_secret,
                encryption_secret,
                clickhouse_url_secret,
                clickhouse_user_secret,
                clickhouse_password_secret,
                clickhouse_migration_url_secret,
                clickhouse_db_secret,
                clickhouse_migration_ssl_secret,
            ]:
                _s.grant_read(task_def.execution_role)
        # Allow the worker task to read/write to the events bucket (v3 event uploads)
        events_bucket.grant_read_write(task_def.task_role)

        # Allow worker to reach RDS/Redis
        worker_sg = worker.connections.security_groups[0]
        rds_sg.add_ingress_rule(peer=worker_sg, connection=ec2.Port.tcp(5432), description="Allow worker to Postgres")
        redis_sg.add_ingress_rule(peer=worker_sg, connection=ec2.Port.tcp(6379), description="Allow worker to Redis")

        CfnOutput(self, "AlbUrl", value=f"http://{web.load_balancer.load_balancer_dns_name}")
        CfnOutput(self, "EventsBucketName", value=events_bucket.bucket_name)
        # Expose ClickHouse secret names to simplify population post-deploy
        CfnOutput(self, "ClickhouseUrlSecretName", value=clickhouse_url_secret.secret_name)
        CfnOutput(self, "ClickhouseUserSecretName", value=clickhouse_user_secret.secret_name)
        CfnOutput(self, "ClickhousePasswordSecretName", value=clickhouse_password_secret.secret_name)
        CfnOutput(self, "ClickhouseMigrationUrlSecretName", value=clickhouse_migration_url_secret.secret_name)
        CfnOutput(self, "ClickhouseDbSecretName", value=clickhouse_db_secret.secret_name)
        CfnOutput(self, "ClickhouseMigrationSslSecretName", value=clickhouse_migration_ssl_secret.secret_name)
        # Core app secret names for easier rotation
        CfnOutput(self, "NextAuthSecretName", value=nextauth_secret.secret_name)
        CfnOutput(self, "SaltSecretName", value=salt_secret.secret_name)
        CfnOutput(self, "EncryptionKeySecretName", value=encryption_secret.secret_name)
        CfnOutput(self, "DatabaseUrlSecretName", value=db_url_secret.secret_name)
        # Convenience outputs for ECS redeploys
        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        CfnOutput(self, "WebServiceName", value=web.service.service_name)
        CfnOutput(self, "WorkerServiceName", value=worker.service_name)
