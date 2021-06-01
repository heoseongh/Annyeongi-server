from packages.musicplayer import MusicPlayer
import re
import sys

from google.cloud import speech

import pyaudio
from six.moves import queue

import uuid
import json
import api.Index as API # 안녕이 서버 모듈 임포트

# 스트림은 연속으로 305초까지만 열어놓을 수 있다.
# TODO 305초 이후에 꺼진 스트림을 다시 열어놓을 방법 생각하기.

# 음성 녹음시에 필요한 파라미터
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

class MicrophoneStream(object):
    """녹음 스트림을 생성한다."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """버퍼에서 계속 오디오 스트림 데이터를 수집한다."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)

def listen_print_loop(responses):
    
    serviceStarted = False
    musicStarted = False
    conversations = []

    num_chars_printed = 0
    for response in responses:
        """
        response 클래스에는 음성에서 텍스트로 변환되어 온 단어 하나하나가 transcript 필드에 담겨있다.
        response 형식은 json과 비슷하다.
        {
            alternatives 
            {
                transcript: "Hello"
            }
            stability: 0.009999999776482582
            result_end_time 
            {
                seconds: 2
                nanos: 250000000
            }
        }
        타입 = <class 'google.cloud.speech_v1.types.cloud_speech.StreamingRecognizeResponse'>
        """
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        
        if not result.alternatives:
            continue
        
        # 실제 변환된 텍스트가 담긴 부분
        transcript = result.alternatives[0].transcript

        # 이전에 출력된 텍스트를 덮어씌우기 위한 공백
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            """
            다음 결과와 같이 이전에 출력된 텍스트를 공백으로 덮어씌우면서 출력하여 마치 하나의 문장인 것 처럼 보여준다.
            >>> 안녕
            >>> 안녕하
            >>> 안녕하세요
            >>> result: 안녕하세요 
            문장의 마지막 단어가 아니라면
            이전에 출력된 텍스트 길이(num_chars_printed)에서 현재 발화의 길이(len(transcript))만큼을 공백으로 덮어씌우고,
            커서를 맨 앞으로 캐리지리턴(carriage return) 한다.
            """
            sys.stdout.write(transcript + overwrite_chars + "\r") 
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            # 안녕이 서비스가 동작하지 않고 있는 경우(serviceStarted == False) 다음의 방법으로 안녕이를 시작할 수 있다.
            if not serviceStarted:
                # 다음의 단어들 중 한 단어 이상 포함시켜서 말하면 안녕이 서비스가 시작된다.
                # start keyword: 시작, 좋은 아침, 안녕, 나왔어
                if re.search(r"\b(시작|좋은 아침|안녕|나왔어)\b", transcript, re.I):
                    serviceStarted = True # 서비스 시작 플래그 셋팅
                    # 안녕이 서비스 시작 멘트
                    print("안녕이 서비스를 시작합니다.")
                    API.toSpeech("안녕이 서비스를 시작합니다.")
                    print('==================================')
                    # 안녕이가 먼저 첫 질문을 건네며 대화를 시작한다.
                    API.toSpeech("오늘 하루 어떠셨나요?") # TODO 스타트를 어떻게 끊을지 생각해봐야 할 듯
                    print("오늘 하루 어떠셨나요?")
                    continue
            
            if serviceStarted:
                if musicStarted:
                    """
                    음악이 재생중인 경우, 음성으로 컨트롤할 수 있는 기능들이다.
                    """
                    # 음악 종료 기능
                    if re.search(r"\b(음악 종료|음악 꺼줘|그만 들을래)\b", transcript, re.I):
                        API.toSpeech("음악 재생을 종료합니다.")
                        musicPlayer.stopMusic()
                        musicStarted = False
                        continue
                    # 다음 음악 재생 기능
                    if re.search(r"\b(다음 노래|다른 음악)\b", transcript, re.I):
                        musicPlayer.stopMusic()
                        API.toSpeech("다음 음악을 재생합니다.")
                        musicPlayer.playNextMusic()
                        continue

                # 안녕이 종료하기 
                # 지정해놓은 단어를 말하면 종료할 수 있다.
                # stop keyword: 종료, 잘자, 잘게, 잔다, 바이바이
                elif re.search(r"\b(종료|잘자|잘게|잔다|바이바이)\b", transcript, re.I):
                    API.toSpeech("안녕이 서비스를 종료합니다.")
                    print("안녕이 서비스를 종료합니다.")
                    # 대화 내용 파일에 저장하기
                    with open('conversation.json', 'w') as f:
                        f.write(json.dumps(conversations, ensure_ascii=False))
                    print("총 " + str(len(conversations)) + "건의 대화가 저장되었습니다.")
                    serviceStarted = False # 서비스 종료 플래그 셋팅
                    continue

                else:
                    """
                    사용자가 안녕이와 대화 가능한 조건은
                    1. 안녕이 서비스가 동작중이고,
                    2. 음악이 재생되고 있지 않는 경우이다.
                    """
                    print('사용자: ' + transcript + overwrite_chars)
                    # 안녕이 답장 받아오기 (답장에는 감정 데이터도 함께 온다.)
                    (answer, emotion) = API.getResponseData(transcript)
                    print('안녕이: ' + answer)
                    print('감정분석: ' + emotion)
                    print('----------------')
                    API.toSpeech(answer) # 답장 음성으로 송출

                    # 만약 감정이 '우울'이라면, 우울한 감정에 맞는 노래를 송출해준다.
                    if(emotion == '우울'):
                        API.toSpeech("제가 음악 한 곡 들려드릴게요. 이 음악 듣고 위로가 되었으면 좋겠어요.")
                        # TODO S3에서 음악파일 다운로드 API 호출
                        # Nagative Music List 목록 받기
                        musicFiles = [
                            "../Music/Nagative/n-1-001.mp3","../Music/Nagative/n-2-001.mp3","../Music/Nagative/n-3-001.mp3"]
                        # 뮤직플레이어 생성 (음악 파일 리스트, 플레이 타입 설정)
                        musicPlayer = MusicPlayer(musicFiles, playType='random')
                        # 음악 재생
                        musicPlayer.playMusic()
                        # 음악이 재생되었다는 플래그 설정
                        musicStarted = True
                        continue
                
                # 대화 배열에 적재하기
                UUID = str(uuid.uuid1()) # 객체 구별을 위한 랜덤 값 생성
                conversation = { "id": UUID, "user": transcript, "answer": answer, "emotion": emotion}
                conversations.append(conversation)

            num_chars_printed = 0

def main():
    print('============= 안녕이 v1 =============')

    # 언어 설정 = ko(한국어)
    # 다른 나라 언어는 아래 링크 참고(들어가서 BCP-47 태그 확인)
    # http://g.co/cloud/speech/docs/languages
    language_code = "ko"

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    # 마이크 스트림 생성
    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest
            (audio_content=content)
            for content in audio_generator
        )
        responses = client.streaming_recognize(streaming_config, requests)

        # 실제로 화면에 뿌려주는 부분
        listen_print_loop(responses)

# python -m [파일명] 으로 실행할 수 있도록 설정
# 배포시 따로 path 설정을 하지 않아도 알아서 name 으로 찾아준다.
if __name__ == "__main__":
    main()