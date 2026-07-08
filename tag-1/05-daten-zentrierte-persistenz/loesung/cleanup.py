"""Tear down the exercise's AWS resources (queue + raw bucket).

Run: uv run python cleanup.py
"""

from config import bucket_name, s3_client, settings, sqs_client


def main() -> None:
    sqs = sqs_client()
    try:
        queue_url = sqs.get_queue_url(QueueName=settings.update_queue_name)["QueueUrl"]
        sqs.delete_queue(QueueUrl=queue_url)
        print(f"deleted queue {settings.update_queue_name}")
    except sqs.exceptions.QueueDoesNotExist:
        pass

    s3 = s3_client()
    bucket = bucket_name()
    try:
        objects = s3.list_objects_v2(Bucket=bucket).get("Contents", [])
        # Key is optional in the API contract — skip entries without one
        keys = [obj["Key"] for obj in objects if "Key" in obj]
        if keys:
            s3.delete_objects(Bucket=bucket, Delete={"Objects": [{"Key": key} for key in keys]})
        s3.delete_bucket(Bucket=bucket)
        print(f"deleted bucket {bucket}")
    except s3.exceptions.NoSuchBucket:
        pass


if __name__ == "__main__":
    main()
