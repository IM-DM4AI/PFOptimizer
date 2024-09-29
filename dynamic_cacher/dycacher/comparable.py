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
    
    @property
    def inter_op_num_threads(self):
        return self.config.inter_op_num_threads
    
    @inter_op_num_threads.setter
    def inter_op_num_threads(self, value):
        self.config.inter_op_num_threads = value

    @property
    def intra_op_num_threads(self):
        return self.config.intra_op_num_threads
    
    @intra_op_num_threads.setter
    def intra_op_num_threads(self, value):
        self.config.intra_op_num_threads = value

