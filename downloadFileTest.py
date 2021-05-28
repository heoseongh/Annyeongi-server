import api.Index as API

local_file = "aws.png"
bucket_file = "emotion/happy/music.png"

API.downloadFile(local_file, bucket_file)