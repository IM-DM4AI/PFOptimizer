# coding=utf-8
from functools import wraps

class ComparableFileObject(object):

    def __init__(self, path, offset) -> None:
        self.path = path
        self.offset = offset

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ComparableFileObject):
            return False
        
        return self.path == value.path and self.offset == value.offset
    
    def __hash__(self) -> int:
        return hash((self.path, self.offset))
    
class ComparableONNXConfig(object):
    def __init__(self, config) -> None:
        self.config = config

    def __eq__(self, value: object) -> bool:
        return True
    
    def __hash__(self) -> int:
        return hash("ort config")

