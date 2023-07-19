# check_attendance_function

Firebase functions 환경에서 출석 체크 시스템을 가동하는데 필요한 코드입니다.

## 시작하기(Dev Container)

1. Docker를 설치합니다.
2. 해당 저장소를 복제합니다.
3. IDE나 VSCode로 열면 모든 환경이 자동으로 설정됩니다. 설정이 완료되면 바로 개발 및 테스트가 가능합니다.(IDE에 따라 Dev Container 사용을 위한 추가 작업이 필요할 수 있습니다.)
4. firebase emulators:start --import sample_data를 입력하여 사전 데이터가 DB에 있는채로 테스트 할 수 있습니다.

## 시작하기(Terminal)

1. 해당 저장소를 복제합니다.
2. venv로 가상 환경을 만듭니다.(`python3 -m venv functions/venv`)
3. 필수 패키지를 설치힙니다.(`pip install -r functions/requirements.txt`)
4. Firebase emulator로 firestore, functions 에뮬레이터를 설치합니다.
5. `firebase emulators:start --import sample_data`를 입력하여 사전 데이터가 DB에 있는채로 테스트 할 수 있습니다.

## 시작하기(InteliiJ)

1. 해당 저장소를 복제합니다.
2. 프로젝트 구조에서 Python SDK추가를 하여 Virtualenv환경으로 functions/venv에 새 환경을 생성합니다.
3. IDE 터미널에서 필수 패키지를 설치힙니다.(`pip install -r functions/requirements.txt`)
4. Firebase emulator로 firestore, functions 에뮬레이터를 설치합니다.
5. `firebase emulators:start --import sample_data`를 입력하여 사전 데이터가 DB에 있는채로 테스트 할 수 있습니다.