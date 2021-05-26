import boto3
import json
import os

from local_data.local_data import aws_credentials

def get_s3_resource():
    return boto3.resource(
        's3',
        aws_access_key_id=aws_credentials['id'],
        aws_secret_access_key=aws_credentials['access_key']
    )

def json_to_bucket(json_data: dict, bucket, filename):
    s3_resource = get_s3_resource()
    s3_resource.Object(
        bucket,
        filename,
    ).put(Body=bytes(json.dumps(json_data).encode('UTF-8')), ACL='public-read')

def s3_to_json(bucket, filename) -> dict:
    file_object = get_s3_resource().Object(bucket, filename)
    file = file_object.get()['Body'].read().decode('utf-8')
    json_data = json.loads(file)
    return json_data
