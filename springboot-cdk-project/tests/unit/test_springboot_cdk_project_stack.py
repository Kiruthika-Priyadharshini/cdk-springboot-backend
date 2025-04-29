import aws_cdk as core
import aws_cdk.assertions as assertions

from springboot_cdk_project.springboot_cdk_project_stack import SpringbootCdkProjectStack

# example tests. To run these tests, uncomment this file along with the example
# resource in springboot_cdk_project/springboot_cdk_project_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SpringbootCdkProjectStack(app, "springboot-cdk-project")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
