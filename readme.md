# check_attendance_function

Firebase functions 환경에서 출석 체크를 가능하게 해줍니다.

## 시작하기

1. 해당 저장소를 복제합니다.
2. venv로 가상 환경을 만듭니다.(`python3 -m venv venv`)
3. 필수 패키지인 `firebase_functions`를 설차힙니다.(`pip install firebase_functions`)
4. Firebase emulator로 firestore, functions 에뮬레이터를 설치합니다.
5. `firebase emulators:start --import sample_data`를 입력하여 사전 데이터가 DB에 있는채로 테스트 할 수 있습니다.