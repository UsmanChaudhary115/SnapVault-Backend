# utils/backBlaze_utils.py
from constants import BACKBLAZE_ACCESS_KEY, BACKBLAZE_SECRET_KEY, BACKBLAZE_ENDPOINT, BACKBLAZE_BUCKET_NAME
import boto3
from botocore.client import Config



s3_client = boto3.client(
    's3',
    aws_access_key_id=BACKBLAZE_ACCESS_KEY,
    aws_secret_access_key=BACKBLAZE_SECRET_KEY,
    endpoint_url=BACKBLAZE_ENDPOINT,
    config=Config(signature_version='s3v4')
)

def generate_presigned_url(bucket_name: str, file_key: str, expires_in: int = 3600):
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': file_key},
        ExpiresIn=expires_in
    )