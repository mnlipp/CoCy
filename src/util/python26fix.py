"""
.. codeauthor: mnl
"""

import sys
import imp
import os
from pkg_resources import parse_version
from platform import python_version

# In Python 2.6 there is try/except missing and function may fail.
def getmembers27(obj, predicate=None):
    """Return all members of an object as (name, value) pairs sorted by name.
    Optionally, only return members that satisfy a given predicate."""
    results = []
    for key in dir(obj):
        try:
            value = getattr(obj, key)
        except AttributeError:
            continue
        if not predicate or predicate(value):
            results.append((key, value))
    results.sort()
    return results

class ImpWrapper:

    def __init__(self, path=None):
        if path is not None and not os.path.isdir(path):
            raise ImportError
        self.path = path

    def find_module(self, fullname, path=None):
        subname = fullname.split(".")[-1]
        if subname != fullname and self.path is None:
            return None
        if self.path is None:
            path = None
        else:
            path = [self.path]
        try:
            file, filename, stuff = imp.find_module(subname, path)
        except ImportError:
            return None
        return ImpLoader(file, filename, stuff)


class ImpLoader:

    def __init__(self, file, filename, stuff):
        self.file = file
        self.filename = filename
        self.stuff = stuff

    def load_module(self, fullname):
        mod = imp.load_module(fullname, self.file, self.filename, self.stuff)
        if self.file:
            self.file.close()
        mod.__loader__ = self  # for introspection
        if fullname == "inspect":
            mod.getmembers = getmembers27
        return mod

_fix_applied = False

def install_python26_fix():
    global _fix_applied
    if _fix_applied:
        return
    if cmp(parse_version(python_version()),
           ('00000002', '00000007', '00000000')) < 0:
        #sys.meta_path.append(ImpWrapper())
        sys.path_hooks.append(ImpWrapper)
        try:
            del sys.modules["inspect"]
        except KeyError:
            pass
        sys.path_importer_cache.clear()
    _fix_applied = True
    