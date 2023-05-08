from datetime import datetime, timedelta, timezone
from http import HTTPStatus

from firebase_admin import initialize_app, firestore
from firebase_functions import https_fn, firestore_fn
from google.cloud.firestore_v1 import Client, base_query, DocumentSnapshot

initialize_app()


@https_fn.on_request()
def check_attendance(request: https_fn.Request) -> https_fn.Response:
    """
    외부로부터 출석체크 요청을 받은 경우 적절한 요청인지 분석 후 출결을 진행해주는 함수

    POST 요청 예제: check_attendance?student_id=18017060&student_device_uuid=papp&tag_uuid=we&uid=123

    :param request: Http요청에 대한 정보가 들어간다.(자동으로 할당되는 매개변수)
    :return: 출석체크가 수행된 경우 서버에 등록되었음과 함께 응답코드 200이 반환되고 그렇지
    않은 경우 오류에 관한 정보를 반환한다.

    :rtype: https_fn.Response
    """
    client: Client = firestore.client()
    args = request.args
    snapshot = client.collection('students') \
        .where(filter=base_query.FieldFilter('device_uuid', '==', args.get("device_uuid"))) \
        .get()
    try:
        student = Student(snapshot.__iter__().__next__())
        attendance = Attendance(student, args.get('tag_uuid'))
        (_, document_ref) = client.collection(f'attendance_history/student/{args.get("uid")}') \
            .add(document_data=attendance.to_firestore())
        client.collection(f'attendance_history/professor/{attendance.professor.uid}') \
            .add(document_data=attendance.to_firestore(ref_id=document_ref.id))
        return https_fn.Response(f'{document_ref.id} added on attendance history at {attendance.timestamp}.')
    except StopIteration:
        return https_fn.Response(f'{args.get("student_device_uuid")} is not available.', status=HTTPStatus.UNAUTHORIZED)


@firestore_fn.on_document_created(document='messages/{documentId}')
def auto_upper(event: firestore_fn.Event[firestore_fn.DocumentSnapshot]):
    """
    해당 코드는 예제 코드입니다.
    :param event:
    :return:
    """
    print(f'Uppercasing at {event.params["documentId"]}')
    original: str = event.data.get('data')
    event.data.reference.set({'data': original.upper()})


@firestore_fn.on_document_updated(document='attendance_history/professor/{professor_uid}/*')
def update_attendance(event: firestore_fn.Event[firestore_fn.Change[firestore_fn.DocumentSnapshot]]):
    """
    강의자가 출결 정보를 변경하였을 시 학생용 출결기록 DB에도 변경사항을 반영하는 함수
    :param event: Firestore의 이벤트가 들어간다(자동으로 할당되는 매개변수)
    :return:
    """
    after: firestore_fn.DocumentSnapshot = event.data.after
    student_id: str = event.data.before.get('student_id')
    ref_id: str = event.data.before.get('ref_id')
    client: Client = firestore.client()
    snapshot = client.collection('students') \
        .where(filter=base_query.FieldFilter('student_id', '==', student_id)) \
        .get()
    try:
        id = snapshot.__iter__().__next__().id
        client.collection(f'attendance_history/student/{id}') \
            .document(ref_id) \
            .update({'result': after.get('result')})
        print(f'Update attendance information (result is now {after.get("result")}).')
    except StopIteration:
        print('Can not find professor with id')


class Student:
    def __init__(self, document_snapshot: DocumentSnapshot):
        """
        Firestore로부터 `Student`객체를 생성한다.
        :param document_snapshot: Firestore에서 받아온 응답에 해당된다.
        """
        self.name = document_snapshot.get('name')
        self.student_id = document_snapshot.get('student_id')


class Subject:
    def __init__(self, document_snapshot: DocumentSnapshot):
        """
        Firestore로부터 `Subject`객체를 생성한다.
        :param document_snapshot: Firestore에서 받아온 응답에 해당된다.
        """
        self.day_week: int = document_snapshot.get('day_week')
        self.department: str = document_snapshot.get('department')
        self.end_at: str = document_snapshot.get('end_at')
        self.id: str = document_snapshot.get('id')
        self.major: str = document_snapshot.get('major')
        self.name: str = document_snapshot.get('name')
        self.professor_id: str = document_snapshot.get('professor_id')
        self.start_at: str = document_snapshot.get('start_at')
        self.tag_uuid: str = document_snapshot.get('tag_uuid')
        self.valid_time = document_snapshot.get('valid_time')


class Professor:
    def __init__(self, document_snapshot: DocumentSnapshot):
        """
        강의자에 대한 정보를 가진 객체이다.
        :param document_snapshot: Firestore에서 받아온 응답에 해당된다.
        """
        self.id = document_snapshot.get('id')
        self.name = document_snapshot.get('name')
        self.uid = document_snapshot.id


class Attendance:
    def __init__(self, student: Student, tag_uuid: str):
        """
        학생의 출결에 관한 정보를 가지고 있는 객체이다.
        :param student: `Student`형태의 학생 객체이다.
        :param tag_uuid: 강의실의 고유 ID이다.
        """
        self.tag_uuid = tag_uuid
        self.timestamp = datetime.now(timezone(timedelta(hours=9)))
        self.subject = self.__get_subject()
        self.professor = self.__get_professor()
        self.student = student
        self.result = 'ok'

    def to_firestore(self, ref_id: str = None) -> dict:
        """
        Firebase에 저장하기 위한 형태로 객체를 변환해주는 메서드이다.
        :return: Firestore에 값을 추가할 때 사용되는 반환값
        """
        if ref_id is not None:
            return {
                'ref_id': ref_id,
                'student_id': self.student.student_id,
                'student_name': self.student.name,
                'subject_name': self.subject.name,
                'result': self.result,
                'timestamp': str(self.timestamp.time())
            }
        return {
            'professor_name': self.professor.name,
            'student_id': self.student.student_id,
            'student_name': self.student.name,
            'subject_name': self.subject.name,
            'result': self.result,
            'timestamp': str(self.timestamp.time())
        }

    def __get_subject(self) -> Subject:
        """
        강의실 태그 UUID와 현재 시간을 이용해 과목의 정보를 가져오는 메서드이다.
        :return: 과목의 정보를 반환한다.
        """
        client: Client = firestore.client()
        # TODO: 타임스탬프 개선 이후 정보와 현재 타임 스탬프를 비교하여 연산 필요
        snapshot = client.collection('subjects') \
            .where(filter=base_query.FieldFilter('tag_uuid', '==', self.tag_uuid)) \
            .where(filter=base_query.FieldFilter('day_week', '==', self.timestamp.weekday())) \
            .get()
        try:
            return Subject(snapshot.__iter__().__next__())
        except StopIteration:
            print('Can not get subject info (subject no exist.)')

    def __get_professor(self) -> Professor:
        """
        객체의 강의자 ID를 통해 강의자의 이름을 알아오는 메서드
        :return: 강의자에 대한 정보를 가진 객체
        """
        client: Client = firestore.client()
        snapshot = client.collection('professors') \
            .where(filter=base_query.FieldFilter('id', '==', self.subject.professor_id)) \
            .get()
        try:
            return Professor(snapshot.__iter__().__next__())
        except StopIteration:
            print('Can not find professor with id')
