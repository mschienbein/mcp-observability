#!/usr/bin/env python3
"""
CloudFront distribution add-on for LibreChat HTTPS access
"""

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct


class CloudFrontAddon(Construct):
    """Add CloudFront distribution to existing LibreChat ALB"""
    
    def __init__(self, scope: Construct, id: str, alb_dns_name: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # Create CloudFront distribution
        self.distribution = cloudfront.Distribution(
            self,
            "LibreChatCFDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.HttpOrigin(
                    alb_dns_name,
                    protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                    http_port=80,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,  # Disable caching for dynamic app
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
            ),
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,  # Use only North America and Europe
            enabled=True,
            comment="LibreChat HTTPS Distribution",
        )
        
        # Output the CloudFront URL
        CfnOutput(
            self,
            "CloudFrontURL",
            value=f"https://{self.distribution.distribution_domain_name}",
            description="CloudFront HTTPS URL for LibreChat",
        )