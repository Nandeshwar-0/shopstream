import boto3
from botocore.exceptions import ClientError
from ingestion.config import settings

class MinioClient:
    """Wrapper around boto3 to interact with our local MinIO Data Lake."""

    def __init__(self):
        # We must specify endpoint_url to point to MinIO instead of AWS
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            # Region doesn't matter much for local MinIO, but boto3 complains if missing
            region_name="us-east-1"
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Creates the shopstream-lake bucket if it doesn't already exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            # If a 404 error is thrown, the bucket doesn't exist
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"Bucket {self.bucket} not found. Creating it...")
                self.s3_client.create_bucket(Bucket=self.bucket)
            else:
                raise e

    def upload_file(self, file_path: str, object_name: str) -> bool:
        """
        Uploads a local file to the MinIO bucket.
        :param file_path: Path to the file on the local machine
        :param object_name: Destination path in the S3 bucket (e.g., bronze/orders/file.parquet)
        """
        try:
            self.s3_client.upload_file(file_path, self.bucket, object_name)
            return True
        except ClientError as e:
            print(f"Failed to upload {file_path} to {object_name}: {e}")
            return False
            
    def upload_buffer(self, buffer: bytes, object_name: str) -> bool:
        """
        Uploads bytes directly from memory to MinIO without touching the local disk.
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=object_name,
                Body=buffer
            )
            return True
        except ClientError as e:
            print(f"Failed to upload buffer to {object_name}: {e}")
            return False
