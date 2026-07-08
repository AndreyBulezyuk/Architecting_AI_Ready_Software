"""Tear down the async-job resources (queue + answers table).

Run: uv run python cleanup.py
"""

from config import dynamodb_client, settings, sqs_client


def main() -> None:
    sqs = sqs_client()
    try:
        queue_url = sqs.get_queue_url(QueueName=settings.jobs_queue_name)["QueueUrl"]
        sqs.delete_queue(QueueUrl=queue_url)
        print(f"deleted queue {settings.jobs_queue_name}")
    except sqs.exceptions.QueueDoesNotExist:
        pass

    dynamodb = dynamodb_client()
    try:
        dynamodb.delete_table(TableName=settings.answers_table)
        print(f"deleted table {settings.answers_table}")
    except dynamodb.exceptions.ResourceNotFoundException:
        pass


if __name__ == "__main__":
    main()
