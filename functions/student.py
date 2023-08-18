from google.cloud.firestore_v1 import DocumentSnapshot


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
