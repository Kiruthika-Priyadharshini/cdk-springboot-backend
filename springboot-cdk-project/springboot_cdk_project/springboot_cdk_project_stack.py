from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
)
from constructs import Construct

class SpringbootCdkProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC
        vpc = ec2.Vpc(self, "MyVpc", max_azs=2)

        # Create an ECS Cluster
        cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)

        # Task Definitions
        user_task_def = ecs.FargateTaskDefinition(self, "UserTaskDef")
        user_container = user_task_def.add_container(
            "UserContainer",
            image=ecs.ContainerImage.from_registry("123456789012.dkr.ecr.us-east-1.amazonaws.com/user-service:latest"),
            memory_limit_mib=512,
            cpu=256,
        )
        user_container.add_port_mappings(ecs.PortMapping(container_port=8081))

        order_task_def = ecs.FargateTaskDefinition(self, "OrderTaskDef")
        order_container = order_task_def.add_container(
            "OrderContainer",
            image=ecs.ContainerImage.from_registry("123456789012.dkr.ecr.us-east-1.amazonaws.com/order-service:latest"),
            memory_limit_mib=512,
            cpu=256,
        )
        order_container.add_port_mappings(ecs.PortMapping(container_port=8082))

        # Create a single Application Load Balancer
        lb = elbv2.ApplicationLoadBalancer(self, "LB", vpc=vpc, internet_facing=True)

        listener = lb.add_listener("Listener", port=80, open=True)

        # Create ECS Services
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

        # Attach Services to Load Balancer with different paths
        listener.add_targets("UserTargets",
            priority=10,
            path_patterns=["/user/*"],
            targets=[user_service],
            health_check=elbv2.HealthCheck(path="/user/health", port="8081")
        )

        listener.add_targets("OrderTargets",
            priority=20,
            path_patterns=["/order/*"],
            targets=[order_service],
            health_check=elbv2.HealthCheck(path="/order/health", port="8082")
        )
