import dataclasses
from collections.abc import Mapping
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, overload


FGetType = Callable[[Any], Any]
FSetType = Callable[[Any, Any], None]
FDelType = Callable[[Any], None]
FGet = TypeVar("FGet", bound=FGetType)
FSet = TypeVar("FSet", bound=FSetType)
FDel = TypeVar("FDel", bound=FDelType)

FSET_ATTRIBUTE = "_field_properties_fset"


class BaseFieldProperty(property):
    """Field property base class, allowing to handle default value/factory of field."""

    @staticmethod
    def _default_factory() -> Any:
        raise NotImplementedError

    def __init__(
        self, fget: FGetType, fset: FSetType, fdel: FDelType, doc: Optional[str] = None
    ):
        handle_property_default = None
        if fset is not None:
            # Because fset is overridden, the raw fset is stored in an attribute
            if hasattr(fset, FSET_ATTRIBUTE):
                fset = getattr(fset, FSET_ATTRIBUTE)

            @wraps(fset)
            def handle_property_default(obj, value):
                """Handle field initialization with its default value.

                Field default value will be the class attribute, which is set by the
                descriptor as the property itself. So dataclass __init__ will call the
                property setter with the property as argument; in this case, the default
                factory has to be used."""
                if isinstance(value, BaseFieldProperty):
                    fset(obj, self._default_factory())
                else:
                    fset(obj, value)

            setattr(handle_property_default, FSET_ATTRIBUTE, fset)

        super().__init__(fget=fget, fset=handle_property_default, fdel=fdel, doc=doc)


def to_default_factory(default, default_factory) -> Optional[Callable[[], Any]]:
    assert default is dataclasses.MISSING or default_factory is dataclasses.MISSING
    if default_factory is not dataclasses.MISSING:
        return default_factory
    elif default is not dataclasses.MISSING:
        return lambda: default
    else:
        return None


class FieldPropertyDecorator:
    def __init__(
        self,
        raw: bool,
        inherit: bool,
        *,
        default: Any = dataclasses.MISSING,
        default_factory: Any = dataclasses.MISSING,
        **kwargs,
    ):
        self.raw = raw
        self.inherit = inherit
        self.property: property = property()
        self.kwargs = kwargs
        self.default_factory = to_default_factory(default, default_factory)

    def __call__(self, fget: FGet) -> FGet:
        return self.getter(fget)

    def getter(self, fget: FGet) -> FGet:
        self.property = self.property.getter(fget)
        return fget

    def setter(self, fset: FSet) -> FSet:
        self.property = self.property.setter(fset)
        return fset

    def deleter(self, fdel: FDel) -> FDel:
        self.property = self.property.deleter(fdel)
        return fdel

    def __set_name__(self, owner, name):
        # Get base field from the class MRO if it exists
        for cls in owner.__mro__:
            base_field: Optional[dataclasses.Field] = getattr(
                cls, dataclasses._FIELDS, {}
            ).get(name)
            if base_field is not None:
                # Inherit the attributes if needed
                # (default/default_factory are handled below)
                if self.inherit:
                    for attr in ("init", "repr", "hash", "compare", "metadata"):
                        self.kwargs.setdefault(attr, getattr(base_field, attr))
                # If the inherited field is a field_property, use its accessors
                # as the base accessors of the new property, and inherit default_factory
                # (accessors are always inherited)
                if isinstance(base_field.default, BaseFieldProperty):
                    new_property = base_field.default
                    if self.property.fget is not None:
                        new_property = new_property.getter(self.property.fget)
                    if self.property.fset is not None:
                        new_property = new_property.setter(self.property.fset)
                    if self.property.fdel is not None:
                        new_property = new_property.deleter(self.property.fdel)
                    self.property = new_property
                    if self.inherit and self.default_factory is None:
                        self.default_factory = new_property._default_factory
                # Otherwise, inherit base_field default/default_factory
                elif self.inherit and self.default_factory is None:
                    self.default_factory = to_default_factory(
                        base_field.default, base_field.default_factory
                    )
                break
        # Set default accessors
        if not self.raw:
            hidden_field = "_" + name
            if self.property.fget is None:

                @self.getter
                def default_get(self):
                    return object.__getattribute__(self, hidden_field)

            if self.property.fset is None:

                @self.setter
                def default_set(self, value):
                    object.__setattr__(self, hidden_field, value)

            if self.property.fdel is None:

                @self.deleter
                def default_del(self):
                    object.__delattr__(self, hidden_field)

        # Create field default factory
        if self.default_factory is None:

            def default_factory():
                raise TypeError(f"Missing parameter {name}")

        else:
            default_factory = self.default_factory

        # Create field property and initialize it with registered accessors
        class FieldProperty(BaseFieldProperty):
            _default_factory = staticmethod(default_factory)

        field_prop = FieldProperty(
            self.property.fget, self.property.fset, self.property.fdel
        )
        # Create the dataclass field and set it as final class attribute
        # Field default is set to field property, in order to have the property in the
        # final class namespace
        setattr(owner, name, dataclasses.field(default=field_prop, **self.kwargs))


NO_FIELD = object()

T = TypeVar("T")


@overload
def field_property(
    *,
    init: bool = True,
    repr: bool = True,
    hash: Optional[bool] = None,
    compare: bool = True,
    metadata: Optional[Mapping] = None,
    raw: bool = False,
    inherit: bool = False,
) -> Any:
    ...


@overload
def field_property(
    *,
    default: T,
    init: bool = True,
    repr: bool = True,
    hash: Optional[bool] = None,
    compare: bool = True,
    metadata: Optional[Mapping] = None,
    raw: bool = False,
    inherit: bool = False,
) -> T:
    ...


@overload
def field_property(
    *,
    default_factory: Callable[[], T],
    init: bool = True,
    repr: bool = True,
    hash: Optional[bool] = None,
    compare: bool = True,
    metadata: Optional[Mapping] = None,
    raw: bool = False,
    inherit: bool = False,
) -> T:
    ...


@overload
def field_property(__field: Any) -> FieldPropertyDecorator:
    ...


def field_property(
    __field=NO_FIELD, *, raw: bool = False, inherit: bool = False, **kwargs
):
    """With keywords argument, declare a field property; otherwise, get a property-like
    object from a declared field_property to set its accessors.

    Field property declaration use the same args than dataclass field.
    inherit=True allows to inherit of overridden field parameters (default,
    default_factory, init, repr, hash, compare, metadata)
    raw=True will not add default implementation for field accessors
    """
    if isinstance(__field, FieldPropertyDecorator):
        return __field
    elif __field is not NO_FIELD:
        raise ValueError(f"Invalid field property {__field}")
    else:
        dataclasses.field(**kwargs)  # check that parameters are valid
        return FieldPropertyDecorator(raw, inherit, **kwargs)
