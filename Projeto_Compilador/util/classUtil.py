from functools import wraps 
from types import MethodType

def externalmethod(cls):
    def decorator(func):
        @wraps(func) 
        def wrapper(self, *args, **kwargs): 
            return func(self, *args, **kwargs)

        setattr(cls, func.__name__, wrapper)
        return func
    return decorator

def externalinstancemethod(ins, name: str = None):
    def decorator(func):
        funcName = func.__name__ if (name == None) else name
        setattr(ins, funcName, MethodType(func, ins))
        return func
    return decorator
