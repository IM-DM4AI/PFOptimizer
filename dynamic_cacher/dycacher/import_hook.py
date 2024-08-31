# coding=utf-8

from functools import wraps
import importlib
import sys
from collections import defaultdict
import io

from dycacher.comparable import ComparableFileObject

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

def capture_arguments(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        lookup_args = []
        for elem in args:
            if isinstance(elem, io.BufferedReader):
                lookup_args.append(ComparableFileObject(elem.name))
            else:
                lookup_args.append(elem)
        
        func_namespace = API_CACHE[func.__name__]

        lookup_args = tuple(lookup_args)

        if lookup_args in func_namespace.keys():
            return func_namespace[lookup_args]
        else:
            # print('Calling', func.__name__, args, kwargs)
            ret = func(*args, **kwargs)
            func_namespace[lookup_args] = ret             
            return ret
        
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
