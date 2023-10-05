from google.cloud.firestore_v1 import DocumentSnapshot


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
        self.subject_id = document_snapshot.id

    def to_json(self) -> dict[str, str]:
        """과목의 특정 정보를 JSON 형태로 반환한다.
        Returns:
            강의 이름, 강의 대상 학부 및 전공, 강의 시작 및 종료 시간에 대한 정보를 JSON형태로 반환한다.
        """
        return {
            "department": self.department,
            "major": self.major,
            "start_at": self.start_at,
            "end_at": self.end_at,
            "name": self.name
        }
