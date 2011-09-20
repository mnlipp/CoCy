import collections
from inspect import getmembers
import types
import functools

def component_handlers(component):
    p = lambda x: \
        isinstance(x, collections.Callable) and getattr(x, "handler", False)
    handlers = [v for k, v in getmembers(component, p)]
    return handlers

def replace_targets(component, mapping):
    for handler in component_handlers(component):
        if mapping.has_key(handler.target):
            handler.__dict__["target"] = mapping[handler.target]
