# coding=utf-8

from functools import wraps
import importlib
import sys
from collections import defaultdict
import io
import types

from dycacher.comparable import ComparableFileObject, ComparableONNXConfig
import inspect

_post_import_hooks = defaultdict(list)

API_CACHE = defaultdict(dict)

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

def reuse_checking(func):
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
        
        if isinstance(func, types.MethodType):
            func_namespace = API_CACHE[id(func.__func__)]
        else:
            func_namespace = API_CACHE[id(func)]

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

            print('Calling', func.__name__, args, kwargs)
            ret = func(*args, **call_kw_args)
            print("context object:", ret)
            if isinstance(func, types.MethodType):
                func_namespace[lookup_args] = (func.__self__, ret)
            else:
                func_namespace[lookup_args] = ret             
            return ret
        
    return wrapper


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
