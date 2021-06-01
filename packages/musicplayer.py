"""
    Author: heoseonghyeon
    Version: MusicPlayer v1.0
    Description: 음악을 재생, 종료 시킬 수 있는 모듈입니다.
"""

class MusicPlayer:

    musicFiles = []
    totalMusicCount = 0
    playType = 'random'
    playList = []
    track = 0
    playMusicProcess = None

    #== 생성자 ==#
    def __init__(self, musicFiles, playType):
        """
        musicFiles : 음악 파일
        playType : 재생 타입
            - 'random': 랜덤재생(디폴트)
            - 'order' : 순차재생(TODO 시간 남으면 만들어야지)
        """
        self.musicFiles = musicFiles            # 음악파일 리스트 담기
        self.totalMusicCount = len(musicFiles)  # 음악파일 전체갯수 계산
        self.playType = playType                # 음악재생 타입 설정
        self.playList = self.getRandomPldayList()

    #== Setter ==#
    def setMusicFiles(self, musicFiles):
        self.musicFiles = musicFiles

    def setTrack(self, track):
        self.track = track
    
    def setPlayType(self, playType):
        self.playType = playType

    #====================== 편의 메서드 ======================#
    
    # 재생 타입 변경(랜덤재생 or 순차재생)
    def changePlayType(self, playType):
        self.setPlayType(playType)
        # 타입별 플레이 리스트 셋팅
        if playType == 'random':
            self.playList = self.getRandomPldayList()
        if playType == 'order':
            self.playList = self.getOrderPlayList()

    # TODO 추후에 순차 재생 기능 추가
    def getOrderPlayList(self):
        orderPlayList = []
        return orderPlayList


    # @description 랜덤 플레이 리스트 생성 메서드
    # @return randomPlayList
    def getRandomPldayList(self):
        """
        음악 개수를 받아서 랜덤으로 플레이 리스트를 생성해주는 메서드이다.
        중복 재생을 원하지 않다면, 해당 메서드를 사용하면 된다.
          - musicFiles에서 랜덤으로 음악 파일 재생
          - 음악이 5개라면, 0~4 사이의 랜덤 인덱스 뽑기
          - 해당 인덱스에 해당하는 음악파일 재생
        """
        from random import random
        import random
        randomPlayList = []
        randomNumber = random.randint(0, self.totalMusicCount - 1)
        # print(randomNumber)
        # randomPlayList에 존재하지 않는 값이 나올때까지 랜럼값을 뽑아서 넣는다.
        for i in range(self.totalMusicCount):
            while randomNumber in randomPlayList:
                randomNumber = random.randint(0, self.totalMusicCount - 1)
                # print(randomNumber)
            randomPlayList.append(randomNumber)
        return randomPlayList
        

    # @description 특정 트랙 음악파일 가져오는 메서드
    # @param track (Number)
    # @return randomPlayList (String)
    def getMusicFile(self):
        return self.musicFiles[self.playList[self.track]]

    # @description 음악 재생 메서드
    def playMusic(self):
        import multiprocessing
        from playsound import playsound
        # 재생할 음악 파일 선택
        selectedMusicFile = self.getMusicFile()
        # 음악파일 재생을 위한 프로세스 생성
        self.playMusicProcess = multiprocessing.Process(target=playsound, args=(selectedMusicFile,), daemon=True)
        self.playMusicProcess.start()
        
    # @description 음악 종료 메서드
    def stopMusic(self):
        self.playMusicProcess.terminate()

    # @description 다음 음악 재생 메서드
    def playNextMusic(self):
        """계속해서 다음 트랙을 재생하다가 플레이 리스트 끝까지 오면 다시 처음 트랙을 재생한다."""
        self.track += 1
        if(self.track not in self.playList):
            self.track = 0
            self.playMusic()
        else:
            self.playMusic()
