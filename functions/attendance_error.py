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
