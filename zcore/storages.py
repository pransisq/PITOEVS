# zcore/storages.py

from storages.backends.s3boto3 import S3Boto3Storage

class CustomS3Boto3Storage(S3Boto3Storage):
    location = 'static'

class CustomMediaS3Boto3Storage(S3Boto3Storage):
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False