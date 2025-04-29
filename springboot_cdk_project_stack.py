from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    Duration
)
from constructs import Construct
from typing import Sequence
from aws_cdk.aws_elasticloadbalancingv2 import IApplicationTargetGroup
from typing import cast


class SpringbootCdkProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC
        vpc = ec2.Vpc(self, "MyVpc", max_azs=2)

        # Create an ECS Cluster
        cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)

        # Task Definitions for User and Order Services
        user_task_def = self.create_task_definition("UserTaskDef", "user-service", 8081)
        order_task_def = self.create_task_definition("OrderTaskDef", "order-service", 8082)

        # Create an Application Load Balancer
        lb = elbv2.ApplicationLoadBalancer(self, "LB", vpc=vpc, internet_facing=True)

        # Create a listener for the load balancer on port 80
        listener = lb.add_listener("Listener", port=80, open=True)

        # Create ECS Services for User and Order Services
        user_service = ecs.FargateService(self, "UserService",
                                          cluster=cluster,
                                          task_definition=user_task_def,
                                          desired_count=1,
                                          )

        order_service = ecs.FargateService(self, "OrderService",
                                           cluster=cluster,
                                           task_definition=order_task_def,
                                           desired_count=1,
                                           )

        # Create target groups for the services
        user_target_group = self.create_target_group("UserTargetGroup", user_service, 8081, vpc)
        order_target_group = self.create_target_group("OrderTargetGroup", order_service, 8082, vpc)

        # Attach ECS services to the listener with path patterns
        self.add_service_target(listener, "UserTargets", user_target_group, "/user/*", 10)
        self.add_service_target(listener, "OrderTargets", order_target_group, "/order/*", 20)

        # Add default action to listener
        listener.add_target_groups("DefaultAction",
                                   target_groups=cast(Sequence[IApplicationTargetGroup], 
                                                      [user_target_group, order_target_group])
                                   )

    def create_task_definition(self, resource_id: str, image_name: str, container_port: int) -> ecs.FargateTaskDefinition:
        """Creates a Fargate task definition for a given service."""
        task_def = ecs.FargateTaskDefinition(self, resource_id)

        # Define the container for the task definition
        container = task_def.add_container(
            f"{image_name}Container",
            image=ecs.ContainerImage.from_registry(f"123456789012.dkr.ecr.us-east-1.amazonaws.com/{image_name}:latest"),
            memory_limit_mib=512,
            cpu=256,
        )

        # Add the port mapping to the container
        container.add_port_mappings(ecs.PortMapping(container_port=container_port))
        return task_def

    def create_target_group(self, resource_id: str, service: ecs.FargateService, container_port: int,
                            vpc: ec2.Vpc) -> elbv2.ApplicationTargetGroup:
        """Creates a target group for a given ECS service."""
        return elbv2.ApplicationTargetGroup(self, resource_id,
                                            port=container_port,  # The port the ECS container listens on
                                            protocol=elbv2.ApplicationProtocol.HTTP,
                                            targets=[service],  # Add the ECS service as the target
                                            vpc=vpc,  # Associate target group with the VPC
                                            health_check=elbv2.HealthCheck(
                                                path=f"/health",  # Health check endpoint
                                                port=str(container_port),
                                                interval=Duration.seconds(30)
                                            )
                                            )

    @staticmethod
    def add_service_target(listener: elbv2.ApplicationListener, target_id: str,
                           target_group: elbv2.ApplicationTargetGroup,
                           path_pattern: str, priority: int):
        """Adds an ECS service target to a listener with path pattern."""

        # Explicitly cast target_groups to Sequence[IApplicationTargetGroup]
        listener.add_target_groups(target_id,
                                   priority=priority,
                                   conditions=[elbv2.ListenerCondition.path_patterns([path_pattern])],
                                   target_groups=cast(Sequence[IApplicationTargetGroup], [target_group]))


