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

# @description: S3 클라이언트 연결 메서드
# @return s3 (Object)
def s3ConnectionClient():
    
    # s3 클라이언트 연결
    s3 = boto3.client(
        's3', 
        aws_access_key_id = AWS_ACCESS_KEY, 
        aws_secret_access_key = AWS_SECRET_KEY
    )
    return s3

# @description: S3 리소스 연결 메서드
# @return s3 (Object)
def s3ConnectionResource():
    
    # s3 리소스 연결
    s3 = boto3.resource(
        's3', 
        aws_access_key_id = AWS_ACCESS_KEY, 
        aws_secret_access_key = AWS_SECRET_KEY
    )
    return s3
        

# @description: S3 파일 업로드 메서드
# @param: local_file, bucket_file (string, string)
def uploadFile(local_file, bucket_file):
    
    s3 = s3ConnectionClient() # s3 클라이언트 연결

    # 파일 업로드
    s3.put_object(
        Bucket = BUCKET_NAME, # 버킷 이름
        Body = local_file, # 업로드할 파일 경로
        Key = bucket_file, # 업로드할 파일명
    )

# @description: S3 파일 다운로드 메서드
# @param: local_file, bucket_file (string, string)
def downloadFile(local_file, bucket_file):
    import botocore

    s3 = s3ConnectionResource() # S3 리소스 연결

    try:
        # 파일 다운로드
        s3.Bucket(BUCKET_NAME).download_file(bucket_file, local_file)
        print('파일이 성공적으로 저장되었습니다.')
        
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            print('해당 파일이 S3에 없습니다.')
        else:
            raise
