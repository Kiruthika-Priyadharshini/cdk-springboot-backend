from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_logs as logs,
    aws_elasticloadbalancingv2 as elbv2,
    Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_ecr as ecr,
    aws_events_targets as targets
)
from constructs import Construct
from typing import Sequence
from aws_cdk.aws_elasticloadbalancingv2 import IApplicationTargetGroup
from typing import cast


class SpringbootCdkProjectStack(Stack):
    """
    A CDK stack to deploy a Spring Boot application with ECS, ALB, and Lambda-based scaling.
    """

    # The class name follows Python's PascalCase naming convention.
    # No changes are needed unless you want to rename it for clarity or consistency.
    # Example alternative: SpringBootCdkStack or SpringBootBackendStack

    # Class-level constants
    LAMBDA_RUNTIME = _lambda.Runtime.PYTHON_3_12
    DEFAULT_CLUSTER_NAME = "MyCluster"
    DEFAULT_SERVICE_NAME = "UserService"
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """
        Initializes the SpringbootCdkProjectStack.

        This method sets up the VPC, ECS cluster, task definitions, services, 
        load balancer, target groups, and a Lambda-based scheduler for scaling ECS services.
        """
        super().__init__(scope, construct_id, **kwargs)

        # Create Lambda function for ECS scheduling
        ecs_scheduler_lambda = self.create_ecs_scheduler_lambda()  # Create the Lambda function once

        # Create CloudWatch Event Rules for scaling up and down
        scale_up_rule = events.Rule(
            self, "ScaleUpRule",
            schedule=events.Schedule.cron(hour="11", minute="0"),  # 11:00 AM
        )
        scale_up_rule.add_target(targets.LambdaFunction(ecs_scheduler_lambda))  # Reuse the Lambda function

        scale_down_rule = events.Rule(
            self, "ScaleDownRule",
            schedule=events.Schedule.cron(hour="18", minute="0"),  # 6:00 PM
        )
        scale_down_rule.add_target(targets.LambdaFunction(ecs_scheduler_lambda))  # Reuse the Lambda function

        # Retrieve account ID and region from context
        account_id = self.node.try_get_context("account_id")
        region = self.node.try_get_context("region")

        # Create a VPC
        vpc = ec2.Vpc(self, "MyVpc", max_azs=2)

        # Create an ECS Cluster
        cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)

        # Task Definitions for User and Order Services
        user_task_def = self.create_task_definition("UserTaskDef", "user-service", 8081, account_id, region)
        order_task_def = self.create_task_definition("OrderTaskDef", "order-service", 8082, account_id, region)

        # Create an Application Load Balancer
        lb = elbv2.ApplicationLoadBalancer(self, "LB", vpc=vpc, internet_facing=True)

        # Create a listener for the load balancer on port 80
        listener = lb.add_listener("Listener", port=80, open=True)

        # Create ECS Services for User and Order Services
        user_service = ecs.FargateService(self, "UserService",
                                          cluster=cluster,
                                          task_definition=user_task_def,
                                          desired_count=1,
                                          health_check_grace_period=Duration.minutes(2),
                                          )

        order_service = ecs.FargateService(self, "OrderService",
                                           cluster=cluster,
                                           task_definition=order_task_def,
                                           desired_count=1,
                                           health_check_grace_period=Duration.minutes(2),
                                           )

        # Create target groups for the services
#         user_target_group = self.create_target_group("UserTargetGroup", user_service, 8081, vpc)
        user_target_group = self.create_target_group("UserTargetGroup", user_service, 8081, vpc)
        order_target_group = self.create_target_group("OrderTargetGroup", order_service, 8082, vpc)

        # Attach ECS services to the listener with path patterns
        self.add_service_target(listener, "UserTargets", user_target_group, "/users/*", 10)
        self.add_service_target(listener, "OrderTargets", order_target_group, "/orders/*", 20)

        # Add default action to listener
        listener.add_target_groups("DefaultAction",
                                   target_groups=cast(Sequence[IApplicationTargetGroup],
                                                      [user_target_group, order_target_group])
                                   )
    def create_task_definition(self, resource_id: str, image_name: str, container_port: int, account_id: str, region: str):
        # Create IAM Role for ECS task execution
        execution_role = iam.Role(
            self, f"{resource_id}ExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )

        # Create log group for container logging
        log_group = logs.LogGroup(
            self, f"{resource_id}LogGroup",
            retention=logs.RetentionDays.ONE_WEEK
        )

        # Reference the ECR repository (no need to hardcode the URI)
        repository = ecr.Repository.from_repository_name(
            self, f"{resource_id}EcrRepo", repository_name=image_name
        )

        # Create task definition with custom execution role
        task_def = ecs.FargateTaskDefinition(
            self, resource_id,
            execution_role=execution_role
        )

        # Add container with ECR image and logging
        container = task_def.add_container(
            f"{image_name}Container",
            image=ecs.ContainerImage.from_ecr_repository(repository, tag="latest"),
            memory_limit_mib=512,
            cpu=256,
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="ecs",
                log_group=log_group
            )
        )

        # Port mapping
        container.add_port_mappings(
            ecs.PortMapping(container_port=container_port)
        )

        return task_def


    def create_target_group(self, resource_id: str, service: ecs.FargateService, container_port: int,
                            vpc: ec2.Vpc) -> elbv2.ApplicationTargetGroup:
        """
        Creates a target group for a given ECS service.

        Args:
            resource_id (str): The unique identifier for the target group.
            service (ecs.FargateService): The ECS service to associate with the target group.
            container_port (int): The port the ECS container listens to.
            vpc (ec2.Vpc): The VPC to associate with the target group.

        Returns:
            elbv2.ApplicationTargetGroup: The created target group.
        """
        health_check=elbv2.HealthCheck(path=f"/health",
                                        port=str(container_port),
                                        interval=Duration.seconds(60),
                                        timeout=Duration.seconds(30),
                                        healthy_http_codes="200-499",
                                        )
        return elbv2.ApplicationTargetGroup(self, resource_id,
                                            port=container_port,  # The port the ECS container listens to
                                            protocol=elbv2.ApplicationProtocol.HTTP,
                                            targets=[service],  # Add the ECS service as the target
                                            vpc=vpc,  # Associate target group with the VPC
                                            health_check=health_check
                                            )

    @staticmethod
    def add_service_target(listener: elbv2.ApplicationListener, target_id: str,
                           target_group: elbv2.ApplicationTargetGroup,
                           path_pattern: str, priority: int):
        """
        Adds an ECS service target to a listener with a specified path pattern.

        Args:
            listener (elbv2.ApplicationListener): The listener to attach the target group to.
            target_id (str): The unique identifier for the target group.
            target_group (elbv2.ApplicationTargetGroup): The target group to attach.
            path_pattern (str): The path pattern for routing traffic.
            priority (int): The priority of the rule.
        """
        # Explicitly cast target_groups to Sequence[IApplicationTargetGroup]
        listener.add_target_groups(target_id,
                                   priority=priority,
                                   conditions=[elbv2.ListenerCondition.path_patterns([path_pattern])],
                                   target_groups=cast(Sequence[IApplicationTargetGroup], [target_group]))
    
    def create_ecs_scheduler_lambda(self) -> _lambda.Function:
        """
        Creates a Lambda function for ECS service scaling.

        Returns:
            _lambda.Function: The created Lambda function.
        """
        lambda_env = {
            "CLUSTER_NAME": self.DEFAULT_CLUSTER_NAME,
            "SERVICE_NAME": self.DEFAULT_SERVICE_NAME,
        }

        # Ensure the Lambda code directory exists and is correctly referenced
        return _lambda.Function(
            self,
            "EcsSchedulerLambda",
            runtime=self.LAMBDA_RUNTIME,
            handler="ecs_scheduler.handler",
            code=_lambda.Code.from_asset("lambda"),  # Ensure "lambda" directory exists
            environment=lambda_env
        )


