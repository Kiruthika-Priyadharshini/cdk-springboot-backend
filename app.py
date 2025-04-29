#!/usr/bin/env python3

import aws_cdk as cdk
from springboot_cdk_project_stack import SpringbootCdkProjectStack

app = cdk.App()

# Retrieve account ID and region from context
account = app.node.try_get_context("account_id")
region = app.node.try_get_context("region")

SpringbootCdkProjectStack(app, "SpringbootCdkProjectStack", env=cdk.Environment(
    account=account,
    region=region
))

app.synth()
