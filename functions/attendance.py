from datetime import datetime, timezone, timedelta

from firebase_admin import firestore
from google.cloud.firestore_v1 import Client, base_query

from attendance_error import SubjectNotFoundError, ProfessorNotFoundError
from professor import Professor
from student import Student
from subject import Subject


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
        self.result = 'normal'

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
                'timestamp': self.timestamp.timestamp()
            }
        return {
            'professor_name': self.professor.name,
            'student_id': self.student.student_id,
            'student_name': self.student.name,
            'subject_name': self.subject.name,
            'result': self.result,
            'timestamp': self.timestamp.timestamp()
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
            result = Subject(snapshot.__iter__().__next__())
            # 과목의 시작 시간에 유효시간을 더함으로서 현재 출결 가능한 시간인지 구하는 로직
            end_attendance = datetime.strptime(
                result.start_at[:5], '%H:%M') + timedelta(minutes=result.valid_time)
            if end_attendance.time() < self.timestamp.time():
                raise SubjectNotFoundError
            return result
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
