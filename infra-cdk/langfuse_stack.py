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
    aws_ecr as ecr,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
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

        # ClickHouse secrets are defined later (after optional EC2 provisioning)
        # so that we can default to the instance private IP without circular deps.

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

        # Langfuse Web/Worker are defined later, after ClickHouse secrets

        # --- Optional: provision a single-node ClickHouse on EC2 for free self-hosting
        # Enable by passing: -c PROVISION_CLICKHOUSE_EC2=true
        provision_ch = self.node.try_get_context("PROVISION_CLICKHOUSE_EC2")
        if str(provision_ch).lower() in ["1", "true", "yes"]:
            ch_sg = ec2.SecurityGroup(self, "ClickhouseSg", vpc=vpc, allow_all_outbound=True)
            # Ingress rules will be added after Web/Worker are defined to avoid circular deps

            # Attach an instance role to enable SSM access for diagnostics
            ch_instance_role = iam.Role(
                self,
                "ClickhouseInstanceRole",
                assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),
                    # allow instance to login/pull/push to ECR for mirrored image
                    iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser"),
                ],
            )

            ch_instance = ec2.Instance(
                self,
                "ClickhouseInstance",
                vpc=vpc,
                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL),
                machine_image=ec2.MachineImage.latest_amazon_linux2023(),
                security_group=ch_sg,
                role=ch_instance_role,
                block_devices=[
                    ec2.BlockDevice(
                        device_name="/dev/xvda",
                        volume=ec2.BlockDeviceVolume.ebs(50),  # 50 GB gp3
                    )
                ],
            )
            # Install ClickHouse via Docker (preferred for consistency) or RPM based on context flag
            use_docker = str(self.node.try_get_context("PROVISION_CLICKHOUSE_DOCKER")).lower() in ["1", "true", "yes"]

            if use_docker:
                # Create an ECR repository for mirroring the ClickHouse image, and use a pinned tag via context
                image_tag = self.node.try_get_context("CLICKHOUSE_IMAGE_TAG") or "24.8"
                ch_repo = ecr.Repository(self, "ClickhouseEcrRepo")
                ecr_image_uri = f"{ch_repo.repository_uri}:{image_tag}"
                # Ensure the ECR repo exists before the instance boots and tries to push/pull
                ch_instance.node.add_dependency(ch_repo)

                # Simplified, more robust ClickHouse setup using standard image without custom volume mounts
                ch_instance.user_data.add_commands(
                    "set -euxo pipefail",
                    # Install Docker and AWS CLI
                    "dnf -y install docker awscli || yum -y install docker awscli",
                    "systemctl enable --now docker",
                    "usermod -aG docker ec2-user || true",
                    # ECR login with retry logic
                    f"REGION='{cdk.Aws.REGION}'",
                    f"ECR_IMAGE='{ecr_image_uri}'",
                    f"DOCKER_HUB_IMAGE='clickhouse/clickhouse-server:{image_tag}'",
                    "REGISTRY=$(echo ${ECR_IMAGE} | cut -d'/' -f1)",
                    "for i in {1..3}; do aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${REGISTRY} && break || sleep 5; done",
                    # Robust image pull strategy: try ECR first, fallback to Docker Hub
                    "IMAGE_TO_USE=${DOCKER_HUB_IMAGE}",
                    "if docker pull ${ECR_IMAGE}; then IMAGE_TO_USE=${ECR_IMAGE}; else docker pull ${DOCKER_HUB_IMAGE} && docker tag ${DOCKER_HUB_IMAGE} ${ECR_IMAGE} && docker push ${ECR_IMAGE} || true; fi",
                    # Stop any existing container
                    "docker stop clickhouse || true",
                    "docker rm clickhouse || true",
                    # Run ClickHouse with minimal configuration (no custom volume mounts that cause issues)
                    "docker run -d --name clickhouse --restart unless-stopped -p 8123:8123 -p 9000:9000 ${IMAGE_TO_USE}",
                    # Enhanced health check with retry and fallback
                    "echo 'Waiting for ClickHouse to start...'",
                    "for i in {1..30}; do",
                    "  if curl -fsS http://127.0.0.1:8123/ping >/dev/null 2>&1; then",
                    "    echo 'ClickHouse is healthy and responding on port 8123'",
                    "    break",
                    "  elif [ $i -eq 30 ]; then",
                    "    echo 'ClickHouse failed to start after 150 seconds, attempting restart...'",
                    "    docker restart clickhouse || true",
                    "    sleep 10",
                    "    curl -fsS http://127.0.0.1:8123/ping >/dev/null 2>&1 && echo 'ClickHouse recovered' || echo 'ClickHouse still failing'",
                    "  else",
                    "    echo \"Attempt $i/30: ClickHouse not ready yet, waiting 5 seconds...\"",
                    "    sleep 5",
                    "  fi",
                    "done",
                    # Log final status
                    "docker ps | grep clickhouse || echo 'ClickHouse container not running'",
                    "ss -ltnp | grep -E '(8123|9000)' || echo 'ClickHouse ports not listening'",
                )

            # --- ClickHouse Secrets (default to instance private IP if EC2 is provisioned)
            ch_url_ctx = self.node.try_get_context("CLICKHOUSE_URL")
            ch_user_ctx = self.node.try_get_context("CLICKHOUSE_USER")
            ch_pass_ctx = self.node.try_get_context("CLICKHOUSE_PASSWORD")
            ch_db_ctx = self.node.try_get_context("CLICKHOUSE_DB")
            ch_migr_url_ctx = self.node.try_get_context("CLICKHOUSE_MIGRATION_URL")
            ch_migr_ssl_ctx = self.node.try_get_context("CLICKHOUSE_MIGRATION_SSL")

            ch_ip = ch_instance.instance_private_ip
            ch_url_default = cdk.Fn.join("", ["http://", ch_ip, ":8123"])
            ch_migration_url_default = cdk.Fn.join("", ["clickhouse://", ch_ip, ":9000"])

            clickhouse_url_secret = secretsmanager.Secret(
                self,
                "ClickhouseUrl",
                description="CLICKHOUSE_URL for Langfuse v3 (e.g., https://<host>:8443; do not append ?ssl=...)",
                secret_string_value=SecretValue.unsafe_plain_text(ch_url_ctx or ch_url_default),
            )
            clickhouse_user_secret = secretsmanager.Secret(
                self,
                "ClickhouseUser",
                description="CLICKHOUSE_USER for Langfuse v3",
                secret_string_value=SecretValue.unsafe_plain_text(ch_user_ctx or "default"),
            )
            clickhouse_password_secret = secretsmanager.Secret(
                self,
                "ClickhousePassword",
                description="CLICKHOUSE_PASSWORD for Langfuse v3",
                secret_string_value=SecretValue.unsafe_plain_text(ch_pass_ctx or "clickhouse123"),
            )
            clickhouse_migration_url_secret = secretsmanager.Secret(
                self,
                "ClickhouseMigrationUrl",
                description="CLICKHOUSE_MIGRATION_URL for Langfuse v3 (optional)",
                secret_string_value=SecretValue.unsafe_plain_text(ch_migr_url_ctx or ch_migration_url_default),
            )
            clickhouse_db_secret = secretsmanager.Secret(
                self,
                "ClickhouseDb",
                description="CLICKHOUSE_DB for Langfuse v3 (default: 'default')",
                secret_string_value=SecretValue.unsafe_plain_text(ch_db_ctx or "default"),
            )
            clickhouse_migration_ssl_secret = secretsmanager.Secret(
                self,
                "ClickhouseMigrationSsl",
                description="CLICKHOUSE_MIGRATION_SSL for Langfuse v3 (\"true\" | \"false\")",
                secret_string_value=SecretValue.unsafe_plain_text(ch_migr_ssl_ctx or "false"),
            )

            # --- Langfuse Web behind ALB (after secrets)
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
                        "REDIS_CONNECTION_STRING": f"redis://{redis.attr_redis_endpoint_address}:{redis.attr_redis_endpoint_port}",
                        "LANGFUSE_TRACING_ENVIRONMENT": "prod",
                        "NODE_OPTIONS": "--max-old-space-size=3072",
                        "LANGFUSE_AUTO_CLICKHOUSE_MIGRATION_DISABLED": "true",
                        "LANGFUSE_S3_EVENT_UPLOAD_BUCKET": events_bucket.bucket_name,
                        "LANGFUSE_S3_EVENT_UPLOAD_REGION": cdk.Aws.REGION,
                        "LANGFUSE_S3_EVENT_UPLOAD_PREFIX": "events/",
                        "CLICKHOUSE_CLUSTER_ENABLED": "false",
                    },
                    secrets={
                        "DATABASE_URL": ecs.Secret.from_secrets_manager(db_url_secret),
                        "NEXTAUTH_SECRET": ecs.Secret.from_secrets_manager(nextauth_secret),
                        "SALT": ecs.Secret.from_secrets_manager(salt_secret),
                        "ENCRYPTION_KEY": ecs.Secret.from_secrets_manager(encryption_secret),
                        "CLICKHOUSE_URL": ecs.Secret.from_secrets_manager(clickhouse_url_secret),
                        "CLICKHOUSE_USER": ecs.Secret.from_secrets_manager(clickhouse_user_secret),
                        "CLICKHOUSE_PASSWORD": ecs.Secret.from_secrets_manager(clickhouse_password_secret),
                        "CLICKHOUSE_MIGRATION_URL": ecs.Secret.from_secrets_manager(clickhouse_migration_url_secret),
                        "CLICKHOUSE_DB": ecs.Secret.from_secrets_manager(clickhouse_db_secret),
                        "CLICKHOUSE_MIGRATION_SSL": ecs.Secret.from_secrets_manager(clickhouse_migration_ssl_secret),
                    },
                ),
                health_check_grace_period=Duration.seconds(900),
            )
            web.target_group.configure_health_check(
                path="/",
                port="3000",
                healthy_http_codes="200-399",
                interval=Duration.seconds(10),
                healthy_threshold_count=2,
                unhealthy_threshold_count=3,
            )
            web.target_group.set_attribute("deregistration_delay.timeout_seconds", "30")
            if web.task_definition.default_container:
                web.task_definition.default_container.add_environment(
                    "NEXTAUTH_URL",
                    f"http://{web.load_balancer.load_balancer_dns_name}",
                )
            cfn_web_service = web.service.node.default_child
            if isinstance(cfn_web_service, ecs.CfnService):
                cfn_web_service.deployment_configuration = ecs.CfnService.DeploymentConfigurationProperty(
                    minimum_healthy_percent=0,
                    maximum_percent=200,
                )
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
            events_bucket.grant_read_write(web.task_definition.task_role)

            web_sg = web.service.connections.security_groups[0]
            rds_sg.add_ingress_rule(peer=web_sg, connection=ec2.Port.tcp(5432), description="Allow web to Postgres")
            redis_sg.add_ingress_rule(peer=web_sg, connection=ec2.Port.tcp(6379), description="Allow web to Redis")

            # --- Worker (after secrets)
            task_def = ecs.FargateTaskDefinition(self, "WorkerTaskDef", cpu=512, memory_limit_mib=2048)
            task_def.add_container(
                "Worker",
                image=ecs.ContainerImage.from_registry("langfuse/langfuse-worker:latest"),
                logging=ecs.LogDrivers.aws_logs(stream_prefix="LangfuseWorker"),
                environment={
                    "REDIS_CONNECTION_STRING": f"redis://{redis.attr_redis_endpoint_address}:{redis.attr_redis_endpoint_port}",
                    "LANGFUSE_TRACING_ENVIRONMENT": "prod",
                    "NODE_OPTIONS": "--max-old-space-size=3072",
                    "LANGFUSE_AUTO_CLICKHOUSE_MIGRATION_DISABLED": "true",
                    "LANGFUSE_S3_EVENT_UPLOAD_BUCKET": events_bucket.bucket_name,
                    "LANGFUSE_S3_EVENT_UPLOAD_REGION": cdk.Aws.REGION,
                    "LANGFUSE_S3_EVENT_UPLOAD_PREFIX": "events/",
                    "CLICKHOUSE_CLUSTER_ENABLED": "false",
                },
                secrets={
                    "DATABASE_URL": ecs.Secret.from_secrets_manager(db_url_secret),
                    "NEXTAUTH_SECRET": ecs.Secret.from_secrets_manager(nextauth_secret),
                    "SALT": ecs.Secret.from_secrets_manager(salt_secret),
                    "ENCRYPTION_KEY": ecs.Secret.from_secrets_manager(encryption_secret),
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
            cfn_worker_service = worker.node.default_child
            if isinstance(cfn_worker_service, ecs.CfnService):
                cfn_worker_service.deployment_configuration = ecs.CfnService.DeploymentConfigurationProperty(
                    minimum_healthy_percent=0,
                    maximum_percent=200,
                )
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
            events_bucket.grant_read_write(task_def.task_role)

            worker_sg = worker.connections.security_groups[0]
            rds_sg.add_ingress_rule(peer=worker_sg, connection=ec2.Port.tcp(5432), description="Allow worker to Postgres")
            redis_sg.add_ingress_rule(peer=worker_sg, connection=ec2.Port.tcp(6379), description="Allow worker to Redis")

            # Now that web/worker SGs exist, permit them to reach ClickHouse
            ch_sg.add_ingress_rule(peer=web_sg, connection=ec2.Port.tcp(8123), description="Web to CH HTTP")
            ch_sg.add_ingress_rule(peer=web_sg, connection=ec2.Port.tcp(9000), description="Web to CH Native")
            ch_sg.add_ingress_rule(peer=worker_sg, connection=ec2.Port.tcp(8123), description="Worker to CH HTTP")
            ch_sg.add_ingress_rule(peer=worker_sg, connection=ec2.Port.tcp(9000), description="Worker to CH Native")

            CfnOutput(self, "ClickhouseEc2PrivateIp", value=ch_instance.instance_private_ip)
            CfnOutput(self, "ClickhouseEc2SecurityGroupId", value=ch_sg.security_group_id)

        else:
            # --- ClickHouse Secrets (placeholders when EC2 is not provisioned)
            ch_url_ctx = self.node.try_get_context("CLICKHOUSE_URL")
            ch_user_ctx = self.node.try_get_context("CLICKHOUSE_USER")
            ch_pass_ctx = self.node.try_get_context("CLICKHOUSE_PASSWORD")
            ch_db_ctx = self.node.try_get_context("CLICKHOUSE_DB")
            ch_migr_url_ctx = self.node.try_get_context("CLICKHOUSE_MIGRATION_URL")
            ch_migr_ssl_ctx = self.node.try_get_context("CLICKHOUSE_MIGRATION_SSL")

            clickhouse_url_secret = secretsmanager.Secret(
                self,
                "ClickhouseUrl",
                description="CLICKHOUSE_URL for Langfuse v3 (e.g., https://<host>:8443; do not append ?ssl=...)",
                secret_string_value=SecretValue.unsafe_plain_text(ch_url_ctx or "http://127.0.0.1:8123"),
            )
            clickhouse_user_secret = secretsmanager.Secret(
                self,
                "ClickhouseUser",
                description="CLICKHOUSE_USER for Langfuse v3",
                secret_string_value=SecretValue.unsafe_plain_text(ch_user_ctx or "default"),
            )
            clickhouse_password_secret = secretsmanager.Secret(
                self,
                "ClickhousePassword",
                description="CLICKHOUSE_PASSWORD for Langfuse v3",
                secret_string_value=SecretValue.unsafe_plain_text(ch_pass_ctx or "clickhouse123"),
            )
            clickhouse_migration_url_secret = secretsmanager.Secret(
                self,
                "ClickhouseMigrationUrl",
                description="CLICKHOUSE_MIGRATION_URL for Langfuse v3 (optional)",
                secret_string_value=SecretValue.unsafe_plain_text(ch_migr_url_ctx or "clickhouse://127.0.0.1:9000"),
            )
            clickhouse_db_secret = secretsmanager.Secret(
                self,
                "ClickhouseDb",
                description="CLICKHOUSE_DB for Langfuse v3 (default: 'default')",
                secret_string_value=SecretValue.unsafe_plain_text(ch_db_ctx or "default"),
            )
            clickhouse_migration_ssl_secret = secretsmanager.Secret(
                self,
                "ClickhouseMigrationSsl",
                description="CLICKHOUSE_MIGRATION_SSL for Langfuse v3 (\"true\" | \"false\")",
                secret_string_value=SecretValue.unsafe_plain_text(ch_migr_ssl_ctx or "false"),
            )

            # --- Langfuse Web behind ALB (after secrets)
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
                        "REDIS_CONNECTION_STRING": f"redis://{redis.attr_redis_endpoint_address}:{redis.attr_redis_endpoint_port}",
                        "LANGFUSE_TRACING_ENVIRONMENT": "prod",
                        "NODE_OPTIONS": "--max-old-space-size=3072",
                        "LANGFUSE_AUTO_CLICKHOUSE_MIGRATION_DISABLED": "true",
                        "LANGFUSE_S3_EVENT_UPLOAD_BUCKET": events_bucket.bucket_name,
                        "LANGFUSE_S3_EVENT_UPLOAD_REGION": cdk.Aws.REGION,
                        "LANGFUSE_S3_EVENT_UPLOAD_PREFIX": "events/",
                        "CLICKHOUSE_CLUSTER_ENABLED": "false",
                    },
                    secrets={
                        "DATABASE_URL": ecs.Secret.from_secrets_manager(db_url_secret),
                        "NEXTAUTH_SECRET": ecs.Secret.from_secrets_manager(nextauth_secret),
                        "SALT": ecs.Secret.from_secrets_manager(salt_secret),
                        "ENCRYPTION_KEY": ecs.Secret.from_secrets_manager(encryption_secret),
                        "CLICKHOUSE_URL": ecs.Secret.from_secrets_manager(clickhouse_url_secret),
                        "CLICKHOUSE_USER": ecs.Secret.from_secrets_manager(clickhouse_user_secret),
                        "CLICKHOUSE_PASSWORD": ecs.Secret.from_secrets_manager(clickhouse_password_secret),
                        "CLICKHOUSE_MIGRATION_URL": ecs.Secret.from_secrets_manager(clickhouse_migration_url_secret),
                        "CLICKHOUSE_DB": ecs.Secret.from_secrets_manager(clickhouse_db_secret),
                        "CLICKHOUSE_MIGRATION_SSL": ecs.Secret.from_secrets_manager(clickhouse_migration_ssl_secret),
                    },
                ),
                health_check_grace_period=Duration.seconds(900),
            )
            web.target_group.configure_health_check(
                path="/",
                port="3000",
                healthy_http_codes="200-399",
                interval=Duration.seconds(10),
                healthy_threshold_count=2,
                unhealthy_threshold_count=3,
            )
            web.target_group.set_attribute("deregistration_delay.timeout_seconds", "30")
            if web.task_definition.default_container:
                web.task_definition.default_container.add_environment(
                    "NEXTAUTH_URL",
                    f"http://{web.load_balancer.load_balancer_dns_name}",
                )
            cfn_web_service = web.service.node.default_child
            if isinstance(cfn_web_service, ecs.CfnService):
                cfn_web_service.deployment_configuration = ecs.CfnService.DeploymentConfigurationProperty(
                    minimum_healthy_percent=0,
                    maximum_percent=200,
                )
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
            events_bucket.grant_read_write(web.task_definition.task_role)

            web_sg = web.service.connections.security_groups[0]
            rds_sg.add_ingress_rule(peer=web_sg, connection=ec2.Port.tcp(5432), description="Allow web to Postgres")
            redis_sg.add_ingress_rule(peer=web_sg, connection=ec2.Port.tcp(6379), description="Allow web to Redis")

            # --- Worker (after secrets)
            task_def = ecs.FargateTaskDefinition(self, "WorkerTaskDef", cpu=512, memory_limit_mib=2048)
            task_def.add_container(
                "Worker",
                image=ecs.ContainerImage.from_registry("langfuse/langfuse-worker:latest"),
                logging=ecs.LogDrivers.aws_logs(stream_prefix="LangfuseWorker"),
                environment={
                    "REDIS_CONNECTION_STRING": f"redis://{redis.attr_redis_endpoint_address}:{redis.attr_redis_endpoint_port}",
                    "LANGFUSE_TRACING_ENVIRONMENT": "prod",
                    "NODE_OPTIONS": "--max-old-space-size=3072",
                    "LANGFUSE_AUTO_CLICKHOUSE_MIGRATION_DISABLED": "true",
                    "LANGFUSE_S3_EVENT_UPLOAD_BUCKET": events_bucket.bucket_name,
                    "LANGFUSE_S3_EVENT_UPLOAD_REGION": cdk.Aws.REGION,
                    "LANGFUSE_S3_EVENT_UPLOAD_PREFIX": "events/",
                    "CLICKHOUSE_CLUSTER_ENABLED": "false",
                },
                secrets={
                    "DATABASE_URL": ecs.Secret.from_secrets_manager(db_url_secret),
                    "NEXTAUTH_SECRET": ecs.Secret.from_secrets_manager(nextauth_secret),
                    "SALT": ecs.Secret.from_secrets_manager(salt_secret),
                    "ENCRYPTION_KEY": ecs.Secret.from_secrets_manager(encryption_secret),
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
            cfn_worker_service = worker.node.default_child
            if isinstance(cfn_worker_service, ecs.CfnService):
                cfn_worker_service.deployment_configuration = ecs.CfnService.DeploymentConfigurationProperty(
                    minimum_healthy_percent=0,
                    maximum_percent=200,
                )
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
            events_bucket.grant_read_write(task_def.task_role)

            worker_sg = worker.connections.security_groups[0]
            rds_sg.add_ingress_rule(peer=worker_sg, connection=ec2.Port.tcp(5432), description="Allow worker to Postgres")
            redis_sg.add_ingress_rule(peer=worker_sg, connection=ec2.Port.tcp(6379), description="Allow worker to Redis")

        # Create CloudFront distribution for HTTPS
        langfuse_distribution = cloudfront.Distribution(
            self,
            "LangfuseCloudFront",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.HttpOrigin(
                    web.load_balancer.load_balancer_dns_name,
                    protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                    http_port=80,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
            ),
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
            enabled=True,
            comment="Langfuse HTTPS Distribution",
        )

        CfnOutput(self, "AlbUrl", value=f"http://{web.load_balancer.load_balancer_dns_name}")
        CfnOutput(self, "LangfuseHTTPS", value=f"https://{langfuse_distribution.distribution_domain_name}", description="Langfuse HTTPS URL via CloudFront")
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
