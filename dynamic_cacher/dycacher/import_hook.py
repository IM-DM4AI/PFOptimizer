# coding=utf-8

from functools import wraps
import importlib
import sys
from collections import defaultdict
import io
import threading
import types
from enum import Enum, auto

from dycacher.comparable import ComparableFileObject, ComparableONNXConfig
import inspect

_post_import_hooks = defaultdict(list)

API_RULE_MAPPING = defaultdict(dict)

API_CACHE = defaultdict(dict)
CACHE_LOCK = threading.Lock()
global_thread_id = 0

SHM_CACHE_NAME = "dycacher_shm_cache"

SHM_CACHE_SIZE = 1024*1024*1024

class CacheRules(Enum):
    PICKLE = auto()
    JOBLIB = auto()
    ONNXRUNTIME = auto()
    XGBOOST = auto()
    LIGHTGBM = auto()
    TENSORFLOW = auto()
    TORCH = auto()

class PostImportFinder:
    def __init__(self):
        self._skip = set()

    def find_module(self, fullname, path=None):
        if fullname in self._skip:
            return None
        self._skip.add(fullname)
        return PostImportLoader(self)

class PostImportLoader:
    def __init__(self, finder):
        self._finder = finder

    def load_module(self, fullname):
        importlib.import_module(fullname)
        module = sys.modules[fullname]
        for func in _post_import_hooks[fullname]:
            func(module)
        self._finder._skip.remove(fullname)
        return module

def when_imported(fullname):
    def decorate(func):
        if fullname in sys.modules:
            func(sys.modules[fullname])
        else:
            _post_import_hooks[fullname].append(func)
        return func
    return decorate

def reuse_checking(func, rules):
    @wraps(func)
    def wrapper(*args, **kwargs):
        lookup_args = []
        for elem in args:
            if isinstance(elem, io.BufferedReader):
                lookup_args.append(ComparableFileObject(elem.name, elem.tell()))
            else:
                lookup_args.append(elem)

        for key, value in kwargs.items():
            comp_value = value
            if isinstance(value, io.BufferedReader):
                comp_value = ComparableFileObject(elem.name, elem.tell())
        
            lookup_args.append((key, comp_value))
        
        func_id = id(func.__func__) if isinstance(func, types.MethodType) else id(func)

        API_RULE_MAPPING[func_id] = rules
        
        func_namespace = API_CACHE[rules]

        lookup_args = tuple(lookup_args)

        if lookup_args in func_namespace.keys():
            context_state = func_namespace[lookup_args]
            if isinstance(func, types.MethodType):
                context_object = context_state[0]

                caller_frame = inspect.stack()[1].frame
                target_key = None
                for k, v in caller_frame.f_locals.items():
                    if v is func.__self__:
                        target_key = k
                        break
                
                caller_frame.f_locals[target_key] = context_object
                context_ret = context_state[1]
            else:
                context_ret = context_state
                
            return context_ret
        else:
            call_kw_args = dict()
            for key, value in kwargs.items():
                call_value = value
                if isinstance(value, ComparableONNXConfig):
                    call_value = value.config
                call_kw_args[key] = call_value

            # print('Calling', func.__name__, args, kwargs)
            ret = func(*args, **call_kw_args)
            # print("context object:", ret)
            if isinstance(func, types.MethodType):
                func_namespace[lookup_args] = (func.__self__, ret)
            else:
                func_namespace[lookup_args] = ret             
            return ret

    @wraps(wrapper)
    def wrapper_with_lock(*args, **kwargs):
        global global_thread_id
        local_thread_id = threading.get_ident()
        # print(local_thread_id)
        if CACHE_LOCK.locked() and local_thread_id == global_thread_id:
            ret = wrapper(*args, **kwargs)
        else:
            CACHE_LOCK.acquire()
            global_thread_id = threading.get_ident()
            ret = wrapper(*args, **kwargs)
            global_thread_id = 0
            CACHE_LOCK.release()
        
        return ret
    
    return wrapper_with_lock

def wrap_onnx_config_class(cls):
    @wraps(cls)
    def wrapper(*args, **kwargs):
        return ComparableONNXConfig(cls(*args, **kwargs))

    return wrapper

def decorate_instance_method(cls, method, func):
    @wraps(cls)
    def wrapper(*args, **kwargs):
        instance = cls(*args, **kwargs)
        replace = getattr(instance, method)
        replace = func(replace)
        setattr(instance, method, replace)
        return instance
    
    return wrapper

def reset_cache():
    API_CACHE.clear()

def write_to_shm():
    from multiprocessing.shared_memory import SharedMemory
    import pickle
    import struct
    global API_CACHE

    try:
        shm = SharedMemory(name=SHM_CACHE_NAME)
    except FileNotFoundError:
        shm = SharedMemory(name=SHM_CACHE_NAME, create=True, size=SHM_CACHE_SIZE)

    bi_cache = pickle.dumps(API_CACHE)
    bi_cache_size = len(bi_cache)
    if bi_cache_size > shm.size:
        raise ValueError("SharedMemory size is too small")
    
    int_size = struct.calcsize('I')

    shm.buf[:int_size] = struct.pack('I', bi_cache_size)
    shm.buf[int_size: int_size+bi_cache_size] = bi_cache
    shm.close()

def load_from_shm():
    from multiprocessing.shared_memory import SharedMemory
    import pickle
    import struct

    shm = SharedMemory(name=SHM_CACHE_NAME)

    int_size = struct.calcsize('I')

    bi_cache_size = struct.unpack('I', shm.buf[:int_size])[0]
    cache = pickle.loads(shm.buf[int_size: int_size+bi_cache_size])

    global API_CACHE
    API_CACHE = cache
    shm.close()

def close_shm():
    from multiprocessing.shared_memory import SharedMemory
    try:
        shm = SharedMemory(name=SHM_CACHE_NAME)
        shm.close()
        shm.unlink()
    except FileNotFoundError:
        pass

def try_to_load_cache():
    # If cache is not empty, no need load cache from shared memory or disk.
    if(len(API_CACHE) > 0):
        return False
    try:
        # Try to load cache from shared memory
        load_from_shm()
        return False # No need to load cache from disk
    except FileNotFoundError:
        # No shared memory can laod, return True to indicate that it should load model from disk
        return True


import atexit
atexit.register(close_shm)

# another way for import hooking
# import builtins
# 
# original_import = builtins.__import__
# 
# def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
#     module = original_import(name, globals, locals, fromlist, level)
#     if name == "pickle":
#         print("Hook Begin:", name)
#     return module
# 
# builtins.__import__ = custom_import
# 
# 
