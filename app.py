#!/usr/bin/env python3

import aws_cdk as cdk
from springboot_cdk_project_stack import SpringbootCdkProjectStack

app = cdk.App()
SpringbootCdkProjectStack(app, "SpringbootCdkProjectStack", env=cdk.Environment(
    account='123456789012',
    region='us-east-1'
))

app.synth()
