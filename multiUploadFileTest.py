import api.Index as API

PREFIX = "" # 맨 앞에 '/'를 붙이지 말자. '/' 디렉터리도 생겨서 불편하다.

files = ["index.html", "index.js"]

API.multiUploadFile(files, PREFIX)