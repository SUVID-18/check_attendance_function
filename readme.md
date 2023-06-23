# check_attendance_function

Firebase functions 환경에서 출석 체크 시스템을 가동하는데 필요한 코드입니다.

## ⚠️ 주의
테스트 전 원활한 테스트를 위해 `firebase login`을 먼저 진행해주세요

## 시작하기(Dev Container)

1. Docker를 설치합니다.
2. 해당 저장소를 복제합니다.
3. VSCode로 열면 모든 환경이 자동으로 설정됩니다. 설정이 완료되면 바로 개발 및 테스트가 가능합니다.
4. `firebase emulators:start --import sample_data`를 입력하여 사전 데이터가 DB에 있는채로 테스트 할 수 있습니다.

## 시작하기

1. Python3.11 버전을 설치합니다.
2. 해당 저장소를 복제합니다.
3. venv로 가상 환경을 만듭니다.(`python3 -m venv functions/venv`)
4. 필수 패키지를 설치힙니다.(`pip install -r functions/requirements.txt`)
5. Firebase CLI를 설치합니다.
6. `firebase emulators:start --import sample_data`를 입력하여 사전 데이터가 DB에 있는채로 테스트 할 수 있습니다.
