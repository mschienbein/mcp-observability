#!/usr/bin/env python3
"""
Simplified AWS CDK Stack for LibreChat deployment on ECS Fargate
Without persistent storage for initial deployment
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    Tags,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
    aws_s3 as s3,
    aws_servicediscovery as servicediscovery,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct
import json


class LibreChatStack(Stack):
    """
    Simplified CDK Stack for LibreChat deployment with:
    - LibreChat API service
    - MongoDB database
    - Meilisearch for search functionality
    - Shared networking with proper security groups
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC Configuration
        self.vpc = ec2.Vpc(
            self,
            "LibreChatVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # ECS Cluster with CloudMap namespace
        self.cluster = ecs.Cluster(
            self,
            "LibreChatCluster",
            vpc=self.vpc,
            container_insights=True,
            default_cloud_map_namespace=ecs.CloudMapNamespaceOptions(
                name="librechat.local",
                type=servicediscovery.NamespaceType.DNS_PRIVATE,
            ),
        )

        # S3 bucket for file uploads (add timestamp to make unique)
        import time
        timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
        self.uploads_bucket = s3.Bucket(
            self,
            "LibreChatUploads",
            bucket_name=f"librechat-uploads-{self.account}-{self.region}-{timestamp}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Security Groups
        self.alb_security_group = ec2.SecurityGroup(
            self,
            "LibreChatALBSecurityGroup",
            vpc=self.vpc,
            description="Security group for LibreChat ALB",
            allow_all_outbound=True,
        )
        self.alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow HTTP traffic",
        )
        self.alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "Allow HTTPS traffic",
        )

        self.service_security_group = ec2.SecurityGroup(
            self,
            "LibreChatServiceSecurityGroup",
            vpc=self.vpc,
            description="Security group for LibreChat services",
            allow_all_outbound=True,
        )
        self.service_security_group.add_ingress_rule(
            self.alb_security_group,
            ec2.Port.tcp(3080),
            "Allow traffic from ALB",
        )
        self.service_security_group.add_ingress_rule(
            self.service_security_group,
            ec2.Port.all_traffic(),
            "Allow inter-service communication",
        )

        # Secrets for sensitive configuration with proper key lengths
        self.librechat_secrets = secretsmanager.Secret(
            self,
            "LibreChatSecrets",
            description="LibreChat API keys and sensitive configuration",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({
                    "CREDS_KEY": "d9127bbc2f5e7ce09305371749bbf0a68d9fe411632c6594ca11c6656c3b5071",
                    "CREDS_IV": "a20dcfd54ac01415c6ac69c5775dbc93",
                    "JWT_SECRET": "148f744b31af7daacfa6c2231ea6d084b9837b59d6989d51dfcd7e5a3b94c32f",
                    "JWT_REFRESH_SECRET": "76f6ef98d106c5421cddf681ed635b184cb53b75ee436e8bd2227207faff4448",
                    "MEILI_MASTER_KEY": "c8f5e7ce09305371749bbf0a68d9fe411632c6594ca11c6656c3b5071d9127bb",
                    "OPENAI_API_KEY": "user_provided",
                    "ANTHROPIC_API_KEY": "user_provided",
                    "GOOGLE_API_KEY": "user_provided",
                }),
                generate_string_key="MONGO_URI",
            ),
        )

        # Create MongoDB service
        self._create_mongodb_service()
        
        # Create Meilisearch service
        self._create_meilisearch_service()
        
        # Create LibreChat API service
        self._create_librechat_api_service()

    def _create_mongodb_service(self):
        """Create MongoDB service on ECS"""
        
        # Task Definition for MongoDB
        self.mongodb_task_definition = ecs.FargateTaskDefinition(
            self,
            "MongoDBTaskDef",
            memory_limit_mib=2048,
            cpu=1024,
        )

        # MongoDB Container
        self.mongodb_container = self.mongodb_task_definition.add_container(
            "mongodb",
            image=ecs.ContainerImage.from_registry("mongo:latest"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="mongodb",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            environment={
                "MONGO_INITDB_DATABASE": "LibreChat",
            },
            port_mappings=[
                ecs.PortMapping(
                    container_port=27017,
                    protocol=ecs.Protocol.TCP,
                )
            ],
            command=["mongod", "--noauth"],  # No auth for simplicity
        )

        # MongoDB Service
        self.mongodb_service = ecs.FargateService(
            self,
            "MongoDBService",
            cluster=self.cluster,
            task_definition=self.mongodb_task_definition,
            desired_count=1,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[self.service_security_group],
            service_name="mongodb",
        )

        # Service Discovery for MongoDB
        self.mongodb_service.enable_cloud_map(
            name="mongodb",
            dns_record_type=servicediscovery.DnsRecordType.A,
        )

    def _create_meilisearch_service(self):
        """Create Meilisearch service on ECS"""
        
        # Task Definition for Meilisearch
        self.meilisearch_task_definition = ecs.FargateTaskDefinition(
            self,
            "MeilisearchTaskDef",
            memory_limit_mib=1024,
            cpu=512,
        )

        # Meilisearch Container
        self.meilisearch_container = self.meilisearch_task_definition.add_container(
            "meilisearch",
            image=ecs.ContainerImage.from_registry("getmeili/meilisearch:v1.12.3"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="meilisearch",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            environment={
                "MEILI_HOST": "http://0.0.0.0:7700",
                "MEILI_NO_ANALYTICS": "true",
            },
            secrets={
                "MEILI_MASTER_KEY": ecs.Secret.from_secrets_manager(
                    self.librechat_secrets,
                    field="MEILI_MASTER_KEY",
                ),
            },
            port_mappings=[
                ecs.PortMapping(
                    container_port=7700,
                    protocol=ecs.Protocol.TCP,
                )
            ],
        )

        # Meilisearch Service
        self.meilisearch_service = ecs.FargateService(
            self,
            "MeilisearchService",
            cluster=self.cluster,
            task_definition=self.meilisearch_task_definition,
            desired_count=1,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[self.service_security_group],
            service_name="meilisearch",
        )

        # Service Discovery for Meilisearch
        self.meilisearch_service.enable_cloud_map(
            name="meilisearch",
            dns_record_type=servicediscovery.DnsRecordType.A,
        )

    def _create_librechat_api_service(self):
        """Create the main LibreChat API service with ALB"""
        
        # Task Definition for LibreChat API
        self.librechat_task_definition = ecs.FargateTaskDefinition(
            self,
            "LibreChatTaskDef",
            memory_limit_mib=4096,
            cpu=2048,
        )

        # Grant S3 permissions
        self.uploads_bucket.grant_read_write(self.librechat_task_definition.task_role)

        # LibreChat Container
        self.librechat_container = self.librechat_task_definition.add_container(
            "librechat",
            image=ecs.ContainerImage.from_registry("ghcr.io/danny-avila/librechat:latest"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="librechat",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            environment={
                "HOST": "0.0.0.0",
                "PORT": "3080",
                "MONGO_URI": "mongodb://mongodb.librechat.local:27017/LibreChat",
                "MEILI_HOST": "http://meilisearch.librechat.local:7700",
                "SEARCH": "true",
                "MEILI_NO_ANALYTICS": "true",
                "ALLOW_REGISTRATION": "true",
                "ALLOW_EMAIL_LOGIN": "true",
                "ALLOW_SOCIAL_LOGIN": "false",
                "ALLOW_SOCIAL_REGISTRATION": "false",
                "SESSION_EXPIRY": "900000",
                "REFRESH_TOKEN_EXPIRY": "604800000",
                "DOMAIN_CLIENT": f"http://librechat-{self.account}.{self.region}.elb.amazonaws.com",
                "DOMAIN_SERVER": f"http://librechat-{self.account}.{self.region}.elb.amazonaws.com",
                "DEBUG_LOGGING": "true",
                # Endpoints configuration
                "ENDPOINTS": "openAI,anthropic,google,azureOpenAI",
                # Allow users to provide their own keys
                "OPENAI_API_KEY": "user_provided",
                "ANTHROPIC_API_KEY": "user_provided", 
                "GOOGLE_KEY": "user_provided",
                "AZURE_API_KEY": "user_provided",
                # Disable config file to avoid errors
                "CONFIG_PATH": "",
                # Disable RAG for now
                "RAG_API_URL": "",
                # File upload config
                "FILE_UPLOAD_SIZE_LIMIT": "10",
                # App title
                "APP_TITLE": "LibreChat",
                # Registration
                "ALLOW_UNVERIFIED_EMAIL_LOGIN": "true",
            },
            secrets={
                "CREDS_KEY": ecs.Secret.from_secrets_manager(
                    self.librechat_secrets,
                    field="CREDS_KEY",
                ),
                "CREDS_IV": ecs.Secret.from_secrets_manager(
                    self.librechat_secrets,
                    field="CREDS_IV",
                ),
                "JWT_SECRET": ecs.Secret.from_secrets_manager(
                    self.librechat_secrets,
                    field="JWT_SECRET",
                ),
                "JWT_REFRESH_SECRET": ecs.Secret.from_secrets_manager(
                    self.librechat_secrets,
                    field="JWT_REFRESH_SECRET",
                ),
                "MEILI_MASTER_KEY": ecs.Secret.from_secrets_manager(
                    self.librechat_secrets,
                    field="MEILI_MASTER_KEY",
                ),
            },
            port_mappings=[
                ecs.PortMapping(
                    container_port=3080,
                    protocol=ecs.Protocol.TCP,
                )
            ],
            health_check=ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost:3080/health || exit 1"],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                retries=3,
                start_period=Duration.seconds(60),
            ),
        )

        # Create Fargate Service with ALB
        self.librechat_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "LibreChatService",
            cluster=self.cluster,
            task_definition=self.librechat_task_definition,
            desired_count=1,
            public_load_balancer=True,
            listener_port=80,
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[self.service_security_group],
            service_name="librechat-api",
        )

        # Configure health check
        self.librechat_service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200",
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
            timeout=Duration.seconds(5),
            interval=Duration.seconds(30),
        )

        # Enable Service Discovery
        self.librechat_service.service.enable_cloud_map(
            name="librechat",
            dns_record_type=servicediscovery.DnsRecordType.A,
        )

        # Add service dependencies
        self.librechat_service.service.node.add_dependency(self.mongodb_service)
        self.librechat_service.service.node.add_dependency(self.meilisearch_service)

        # Output the ALB URL
        self.alb_url = self.librechat_service.load_balancer.load_balancer_dns_name

        # Create CloudFront distribution for HTTPS
        self.distribution = cloudfront.Distribution(
            self,
            "LibreChatCloudFront",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.HttpOrigin(
                    self.alb_url,
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
            comment="LibreChat HTTPS Distribution",
        )
        
        # Output CloudFront URL
        CfnOutput(
            self,
            "LibreChatHTTPS",
            value=f"https://{self.distribution.distribution_domain_name}",
            description="LibreChat HTTPS URL via CloudFront",
        )
        
        CfnOutput(
            self,
            "LibreChatHTTP",
            value=f"http://{self.alb_url}",
            description="LibreChat HTTP URL (Direct ALB)",
        )

        # Add tags
        Tags.of(self).add("Project", "LibreChat")
        Tags.of(self).add("Environment", "Demo")
        Tags.of(self).add("ManagedBy", "CDK")