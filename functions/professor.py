from google.cloud.firestore_v1 import DocumentSnapshot


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
