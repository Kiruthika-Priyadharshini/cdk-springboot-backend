import boto3
import os

ecs_client = boto3.client('ecs')


def handler(event, context):
    """
    Handles ECS service scaling events.

    Args:
        event: Contains scaling parameters including desired_count.
        context: Lambda context object.

    Returns:
        dict: ECS update service response or error message.
    """
    try:
        # Retrieve environment variables
        cluster_name = os.environ['CLUSTER_NAME']
        service_name = os.environ['SERVICE_NAME']

        # Validate event input
        if 'desired_count' not in event:
            raise ValueError("Missing 'desired_count' in event payload")

        desired_count = int(event['desired_count'])

        # Update ECS service
        response = ecs_client.update_service(
            cluster=cluster_name,
            service=service_name,
            desiredCount=desired_count
        )
        return {
            "statusCode": 200,
            "body": response
        }

    except Exception as e:
        # Handle errors gracefully
        return {
            "statusCode": 500,
            "error": str(e)
        }
