import sys
import os
# 해당 코드는 s3API를 루트 디렉터리로 올려놓는 것과 같은 효과를 준다. -> 그래야 모듈 임포트시 에러가 뜨지 않는다.
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import boto3
from aws.config import (
    AWS_ACCESS_KEY, 
    AWS_SECRET_KEY, 
    BUCKET_NAME
)

# @description: S3 연결 메서드
def s3Connection():
    
    # s3 연결
    s3 = boto3.client(
        's3', 
        aws_access_key_id = AWS_ACCESS_KEY, 
        aws_secret_access_key = AWS_SECRET_KEY
    )
    return s3

# @description: S3 파일 업로드 메서드
# @param: file_path, file_name (string, string)
def uploadFile(file_path, file_name):
    
    s3 = s3Connection() # s3 연결

    # 파일 업로드
    s3.put_object(
        Bucket = BUCKET_NAME, # 버킷 이름
        Body = file_path, # 업로드할 파일 경로
        Key = file_name, # 업로드할 파일명
    )