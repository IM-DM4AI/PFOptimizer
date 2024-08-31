# coding=utf-8

class ComparableFileObject(object):

    def __init__(self, path) -> None:
        self.path = path

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ComparableFileObject):
            return False
        
        return self.path == value.path
    
    def __hash__(self) -> int:
        return hash((self.path))