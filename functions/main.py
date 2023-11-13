from datetime import datetime, timedelta, timezone

from firebase_admin import initialize_app, firestore, messaging
from firebase_functions import https_fn, firestore_fn
from google.cloud.firestore_v1 import Client, base_query

from attendance import Attendance
from attendance_error import DuplicateAttendanceError
from student import Student
from subject import Subject

initialize_app()


def check_vaild_student(request: https_fn.CallableRequest):
    """유효한 학생인지 확인하는 함수

    제공된 매개변수를 통해 UUID를 분석 후 유효한 학생의 정보를 반환한다.

    Args:
        request: Firebase Function 요청에 대한 정보가 들어간다
    Returns:
        디바이스 UUID와 일치하는 학생의 객체를 반환한다.
    """
    client: Client = firestore.client()
    args = request.data
    snapshot = client.collection('students') \
        .where(filter=base_query.FieldFilter('device_uuid', '==', args.get("device_uuid"))) \
        .get()
    return snapshot


@https_fn.on_call()
def get_all_subjects(request: https_fn.CallableRequest):
    """
    강의실에서 현재 강의가 진행되는 과목의 정보를 가져오는 함수
    Args:
        request: Firebase Function 요청에 대한 정보가 들어간다.(자동으로 할당되는 매개변수)
    Notes:
        해당 함수는 직접 호출이 아닌 Firebase Function에 의해 호출되며 호출 시 아래와 같은 매개변수가 필요하다

        * device_uuid: 학생 기기의 UUID
        * tag_uuid: 태그(강의실) UUID

    Returns:
        특정 강의실에서 진행되는 강의의 목록이 반환된다. 태그 UUID에 해당되는 과목이 없는 경우 오류코드와 함께 오류에 관한 정보를 반환한다.
    """
    args = request.data
    client = firestore.client()
    try:
        subjects = client.collection('subjects') \
            .where(filter=base_query.FieldFilter('tag_uuid', '==', args.get('tag_uuid'))) \
            .where(filter=base_query.FieldFilter('day_week', '==', datetime.now().weekday())) \
            .get()
        return list(map(lambda subject: Subject(subject).to_json(), subjects))
    except StopIteration:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.PERMISSION_DENIED,
                                  message='등록되지 않은 기기입니다.')


@https_fn.on_call()
def check_available_subject(request: https_fn.CallableRequest):
    """
    강의실에서 현재 강의가 진행되는 과목의 정보를 가져오는 함수
    Args:
        request: Firebase Function 요청에 대한 정보가 들어간다.(자동으로 할당되는 매개변수)
    Notes:
        해당 함수는 직접 호출이 아닌 Firebase Function에 의해 호출되며 호출 시 아래와 같은 매개변수가 필요하다

        * device_uuid: 학생 기기의 UUID
        * tag_uuid: 태그(강의실) UUID

    Returns:
        특정 강의실에서 진행되는 강의의 목록이 반환된다. 태그 UUID에 해당되는 과목이 없는 경우 오류코드와 함께 오류에 관한 정보를 반환한다.
    """
    args = request.data
    snapshot = check_vaild_student(request)
    try:
        student = Student(snapshot.__iter__().__next__())
        subject = Attendance(student, args.get('tag_uuid')).subject
        return subject.to_json()
    except StopIteration:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.PERMISSION_DENIED,
                                  message='등록되지 않은 기기입니다.')


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
    snapshot = check_vaild_student(request)
    try:
        student = Student(snapshot.__iter__().__next__())
        attendance = Attendance(student, args.get('tag_uuid'))
        history = client.collection(f'attendance_history/student/{request.auth.uid}') \
            .order_by('timestamp', direction='DESCENDING') \
            .limit(1) \
            .get()
        try:
            timestamp = float(history.__iter__().__next__().get('timestamp'))
            history_time = datetime.fromtimestamp(
                timestamp, timezone(timedelta(hours=9)))
            if (attendance.timestamp.date() == history_time.date()) and \
                    (attendance.timestamp.time().hour == history_time.time().hour):
                print('duplicate')
                raise DuplicateAttendanceError
        except StopIteration:
            pass
        (_, document_ref) = client.collection(f'attendance_history/student/{request.auth.uid}') \
            .add(document_data=attendance.to_firestore())
        client.collection(f'attendance_history/professor/{attendance.professor.uid}') \
            .add(document_data=attendance.to_firestore(ref_id=document_ref.id))
        print(
            f'{document_ref.id} added on attendance history at {attendance.timestamp}.')

    except StopIteration:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.PERMISSION_DENIED,
                                  message='등록되지 않은 기기입니다.')

    except Exception as error:
        print(error)
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT, message=str(error))


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
        student = Student(snapshot.__iter__().__next__())
        student_uid = student.document_id
        client.collection(f'attendance_history/student/{student_uid}') \
            .document(ref_id) \
            .update({'result': after.get('result')})
        print(
            f'Update attendance information (result is now {after.get("result")}).')
        message = messaging.Message(
            notification=messaging.Notification(
                title='출결 정보 변경',
                body='교수님에 의해 %s 과목의 출결 정보가 변경되었습니다.' % event.data.before.get('subject_name')
            ), token=student.token
        )
        response = messaging.send(message)
        print('[ %s ] 메시지를 정상적으로 보냈습니다.' % response)
    except StopIteration:
        print('대상 학생이 존재하지 않습니다.')
