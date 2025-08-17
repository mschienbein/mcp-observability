#!/usr/bin/env python3
import os
import aws_cdk as cdk
from langfuse_stack import LangfuseStack

app = cdk.App()

# Ensure we use the same bootstrap qualifier as the environment
synth = cdk.DefaultStackSynthesizer(qualifier="mcpobs")

LangfuseStack(
    app,
    "LangfuseStack",
    synthesizer=synth,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()
