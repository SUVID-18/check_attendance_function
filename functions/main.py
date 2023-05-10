from datetime import datetime, timedelta, timezone

from firebase_admin import initialize_app, firestore
from firebase_functions import https_fn, firestore_fn
from google.cloud.firestore_v1 import Client, base_query, DocumentSnapshot

initialize_app()


@https_fn.on_call()
def check_attendance(request: https_fn.CallableRequest):
    """출석 확인을 진행하는 함수

    외부로부터 출석확인 요청을 받은 경우 적절한 요청인지 분석 후 출결을 진행해주는 함수
    Args:
        request: Firebase Function 요청에 대한 정보가 들어간다.(자동으로 할당되는 매개변수)
    Notes:
        해당 함수는 직접 호출이 아닌 Firebase Function에 의해 호출되며 호출 시 아래와 같은 매개변수가 필요하다

        * device_uuid: 학생 기기의 UUID
        * tag_uuid: 태그(강의실) UUID
    Returns:
        출석체크가 수행된 경우 서버에 등록되었음과 함께 응답코드 200이 반환되고 그렇지 않은 경우 오류코드와 함께 오류에 관한 정보를 반환한다.
    Raises:
        ProfessorNotFoundError: 강의자 ID를 통해 강의자를 찾지 못한 경우
        SubjectNotFoundError: 과목을 찾을 수 없거나 출석 유효시간이 지났을 때
    """
    client: Client = firestore.client()
    args = request.data
    snapshot = client.collection('students') \
        .where(filter=base_query.FieldFilter('device_uuid', '==', args.get("device_uuid"))) \
        .get()
    try:
        student = Student(snapshot.__iter__().__next__())
        attendance = Attendance(student, args.get('tag_uuid'))
        (_, document_ref) = client.collection(f'attendance_history/student/{request.auth.uid}') \
            .add(document_data=attendance.to_firestore())
        client.collection(f'attendance_history/professor/{attendance.professor.uid}') \
            .add(document_data=attendance.to_firestore(ref_id=document_ref.id))
        print(f'{document_ref.id} added on attendance history at {attendance.timestamp}.')

    except Exception as error:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.NOT_FOUND, message=str(error))


@firestore_fn.on_document_updated(document='attendance_history/professor/{professor_uid}/*')
def update_attendance(event: firestore_fn.Event[firestore_fn.Change[firestore_fn.DocumentSnapshot]]):
    """강의자가 출결 정보를 변경하였을 시 학생용 출결기록 DB에도 변경사항을 반영하는 함수
    Args:
         event: Firestore의 이벤트가 들어간다(자동으로 할당되는 매개변수)
    """
    after: firestore_fn.DocumentSnapshot = event.data.after
    student_id: str = event.data.before.get('student_id')
    ref_id: str = event.data.before.get('ref_id')
    client: Client = firestore.client()
    snapshot = client.collection('students') \
        .where(filter=base_query.FieldFilter('student_id', '==', student_id)) \
        .get()
    try:
        student_uid = snapshot.__iter__().__next__().id
        client.collection(f'attendance_history/student/{student_uid}') \
            .document(ref_id) \
            .update({'result': after.get('result')})
        print(f'Update attendance information (result is now {after.get("result")}).')
    except StopIteration:
        print('대상 학생이 존재하지 않습니다.')


class SubjectNotFoundError(Exception):

    def __init__(self):
        super().__init__('강의를 찾을 수 없습니다.(출결 시간 초과)')
        print('Can not get subject info (subject no exist.)')


class ProfessorNotFoundError(Exception):
    """강의자 정보를 찾을 수 없을 때 발생하는 예외"""

    def __init__(self):
        super().__init__('강의자 정보를 확인할 수 없습니다.')
        print('Can not find professor with id')


class DuplicateAttendanceError(Exception):
    """출결 정보가 중복될 때 발생하는 예외"""

    def __init__(self) -> None:
        super().__init__('이미 출결 처리된 과목입니다.')
        print('already completed attendance check')


class Student:
    """학생에 대한 정보에 해당하는 클래스
    출결 시 학생 정보 조회를 위해 사용되는 클래스
    Attributes:
       name: 학생의 이름
       student_id: 학번
    """

    def __init__(self, document_snapshot: DocumentSnapshot):
        """Firestore로부터 `Student`객체를 생성한다.
        Args:
            document_snapshot: Firestore에서 받아온 응답에 해당된다.
        """
        self.name: str = document_snapshot.get('name')
        self.student_id: str = document_snapshot.get('student_id')


class Subject:
    """과목에 대한 정보에 해당하는 클래스
    출결 시 과목 정보 조회를 위해 사용되는 클래스
    Attributes:
        day_week: 수업 진행 요일(0: 월요일, 1: 화요일, ... , 6: 일요일)
        department: 수강 대상 학부
        end_at: 강의 종료 시간
        id: 과목 ID
        major: 수강 대상 전공
        name: 과목 이름
        professor_id: 강의자의 교번
        start_at: 강의 시작 시간
        tag_uuid: 태그(강의실) UUID
        valid_time: 출결 유효 시간
    """

    def __init__(self, document_snapshot: DocumentSnapshot):
        """Firestore로부터 `Subject`객체를 생성한다.
        Args:
            document_snapshot: Firestore에서 받아온 응답에 해당된다.
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
    """강의자에 대한 정보에 해당하는 클래스
    출결 시 강의자의 정보 조회를 위해 사용되는 클래스
    Attributes:
       id: 강의자의 교번
       name: 강의자 이름
       uid: 강의자의 UID
    """

    def __init__(self, document_snapshot: DocumentSnapshot):
        """강의자에 대한 정보를 가진 객체이다.
        Args:
            document_snapshot: Firestore에서 받아온 응답에 해당된다.
        """
        self.id = document_snapshot.get('id')
        self.name = document_snapshot.get('name')
        self.uid = document_snapshot.id


class Attendance:
    def __init__(self, student: Student, tag_uuid: str):
        """학생의 출결에 관한 정보를 가지고 있는 객체이다.
        Args:
            student: Student형태의 학생 객체이다.
            tag_uuid: 강의실의 고유 ID이다.
        """
        self.tag_uuid = tag_uuid
        self.timestamp = datetime.now(timezone(timedelta(hours=9)))
        self.subject = self.__get_subject()
        self.professor = self.__get_professor()
        self.student = student
        self.result = 'ok'

    def to_firestore(self, ref_id: str = None) -> dict:
        """Firebase에 저장하기 위한 형태로 객체를 변환해주는 메서드이다.
        Args:
            ref_id (optional): 학생용 출결 기록 컬렉션의 문서 ID
        Returns:
            Firestore에 값을 추가할 때 사용되는 반환값
        """
        if ref_id is not None:
            return {
                'ref_id': ref_id,
                'student_id': self.student.student_id,
                'student_name': self.student.name,
                'subject_name': self.subject.name,
                'result': self.result,
                'timestamp': str(self.timestamp)
            }
        return {
            'professor_name': self.professor.name,
            'student_id': self.student.student_id,
            'student_name': self.student.name,
            'subject_name': self.subject.name,
            'result': self.result,
            'timestamp': str(self.timestamp)
        }

    def __get_subject(self) -> Subject:
        """강의실 태그 UUID와 현재 시간을 이용해 과목의 정보를 가져오는 메서드이다.
        Returns:
            과목의 정보를 반환한다.
        Raises:
            SubjectNotFoundError: 과목을 찾을 수 없거나 출석 유효시간이 지났을 때
        """
        client: Client = firestore.client()
        snapshot = client.collection('subjects') \
            .where(filter=base_query.FieldFilter('tag_uuid', '==', self.tag_uuid)) \
            .where(filter=base_query.FieldFilter('day_week', '==', self.timestamp.weekday())) \
            .where(filter=base_query.FieldFilter('start_at', '>=', str(self.timestamp.time()))) \
            .get()
        try:
            return Subject(snapshot.__iter__().__next__())
        except StopIteration:
            raise SubjectNotFoundError

    def __get_professor(self) -> Professor:
        """객체의 강의자 ID를 통해 강의자의 이름을 알아오는 메서드
        Returns:
            강의자에 대한 정보를 가진 객체
        Raises:
            ProfessorNotFoundError: 강의자 ID를 통해 강의자를 찾지 못한 경우
        """
        client: Client = firestore.client()
        snapshot = client.collection('professors') \
            .where(filter=base_query.FieldFilter('id', '==', self.subject.professor_id)) \
            .get()
        try:
            return Professor(snapshot.__iter__().__next__())
        except StopIteration:
            raise ProfessorNotFoundError
