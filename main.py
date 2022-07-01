import builtins
import inspect
from functools import wraps

from forbiddenfruit import cursed, curse


def get_unbound_vars(func) -> set[str]:
    """
    this is a snippet from the 'inspect' module
    :param func: a function
    :return: all the unbound variables
    """
    code = func.__code__
    global_ns = func.__globals__
    builtin_ns = global_ns.get("__builtins__", builtins.__dict__)
    if inspect.ismodule(builtin_ns):
        builtin_ns = builtin_ns.__dict__
    unbound_names: set = set()

    for name in code.co_names:
        if name in ("None", "True", "False") or name in global_ns or name in builtin_ns:
            # Because these used to be builtins instead of keywords, they
            # may still show up as name references. We ignore them.
            continue
        unbound_names.add(name)
    return unbound_names


class CClass(type):
    def __new__(mcs, *args, **kwargs):
        if '__init__' not in args[2]:
            raise Exception("Must implement an __init__ function!")
        vars_ = get_unbound_vars(args[2]['__init__']) - (set(args[2].keys()) | {args[0], })
        args[2]["__slots__"] = vars_

        def __getattribute__(self, name):
            attr = object.__getattribute__(self, name)
            if getattr(attr, "access", 0) == 2 and not getattr(__getattribute__, "inside", False):
                raise AttributeError("Accessing private function")
            if getattr(attr, "access", 0) == 1 and not getattr(__getattribute__, "inside", False):
                raise AttributeError("Accessing protected function")
            return attr

        for name, func in [(key, val) for key, val in args[2].items() if inspect.isfunction(val)]:
            def wrapper(self, *fargs, __f=func, **fkwargs):
                self.__class__.__getattr__ = object.__getattribute__
                ret = __f(self, *fargs, **fkwargs)
                if hasattr(self.__class__, '__getattr__'):
                    del self.__class__.__getattr__
                return ret

            args[2][name] = wraps(func)(wrapper)

        args[2]["__getattribute__"] = __getattribute__

        return super(CClass, mcs).__new__(mcs, *args, **kwargs)


def private(f):
    """
    sets the scope to private (aka 2)
    :param f: function or method
    :return: f
    """
    f.access = 2
    return f


def protected(f):
    """
    sets the scope to protected (aka 1)
    :param f: function or method
    :return: f
    """
    f.access = 1
    return f


class Foo(metaclass=CClass):
    c = 5

    def __init__(self):
        self.a = 10
        self.b: int = 5

    def pub(self):
        print("pub")
        self.prot()

    @private
    def priv(self):
        print("priv")
        pass

    @protected
    def prot(self):
        print("prot")
        pass


class Bar(Foo):
    def __init__(self):
        self.d = "hello"
        super(Bar, self).__init__()

bar = Bar()
bar.pub()
bar.prot()

foo = Foo()
foo.pub()
foo.priv()
foo.prot()