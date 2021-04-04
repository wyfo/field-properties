from typing import TypeVar, cast


class PropertyUnwraper:
    _obj_attr = "obj"

    def __init__(self, obj):
        object.__setattr__(self, PropertyUnwraper._obj_attr, obj)

    def __getattribute__(self, name):
        obj = object.__getattribute__(self, PropertyUnwraper._obj_attr)
        return getattr(obj, "_" + name)

    def __setattr__(self, name, value):
        obj = object.__getattribute__(self, PropertyUnwraper._obj_attr)
        setattr(obj, "_" + name, value)

    def __delattr__(self, name):
        obj = object.__getattribute__(self, PropertyUnwraper._obj_attr)
        delattr(obj, "_" + name)


T = TypeVar("T")


def unwrap_property(self: T) -> T:
    return cast(T, PropertyUnwraper(self))
