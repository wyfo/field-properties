from dataclasses import FrozenInstanceError, InitVar, dataclass, field
from typing import Optional
from unittest.mock import Mock

from pytest import mark, raises

from field_properties import field_property, unwrap_property
from field_properties.field_properties import FSET_ATTRIBUTE


def test_default_field_property():
    @dataclass
    class Foo:
        bar: int = field_property()

    foo = Foo(0)
    assert foo.__dict__ == {"_bar": 0}
    assert foo.bar == 0
    del foo.bar
    assert foo.__dict__ == {}
    with raises(AttributeError):
        _ = foo.bar


def test_field_property():
    global_bar: Optional[int] = None

    @dataclass
    class Foo:
        bar: int = field_property()

        @field_property(bar)
        def get_bar(self) -> int:
            if global_bar is None:
                raise AttributeError("bar")
            return global_bar

        def set_bar(self, value: int):
            nonlocal global_bar
            global_bar = value

        def del_bar(self):
            nonlocal global_bar
            global_bar = None

        set_bar = field_property(bar).setter(set_bar)
        del_bar = field_property(bar).deleter(del_bar)

    foo = Foo(0)
    assert foo.bar == global_bar == 0
    del foo.bar
    with raises(AttributeError):
        _ = foo.bar
    assert global_bar is None


def test_setter_with_default_parameter():
    setter = Mock()
    delattr(setter, FSET_ATTRIBUTE)

    @dataclass
    class WithDefault:
        default: int = field_property(default=0, repr=False)
        field_property(default).setter(setter)

    with_default = WithDefault()
    setter.assert_called_with(with_default, 0)

    @dataclass
    class WithDefaultFactory:
        default_factory: int = field_property(default_factory=lambda: 1, repr=False)
        field_property(default_factory).setter(setter)

    with_default_factory = WithDefaultFactory()
    setter.assert_called_with(with_default_factory, 1)

    @dataclass
    class WithoutDefault:
        no_default: int = field_property(repr=False)
        field_property(no_default).setter(setter)

    with raises(TypeError, match="Missing parameter no_default"):
        WithoutDefault()


def test_inherit_function_has_no_effect():
    @dataclass
    class Foo:
        bar: int = field_property(default=None)

        @field_property(bar)
        def get_bar(self):
            return 0

    @dataclass
    class Foo2(Foo):
        def get_bar(self):
            return 1

    assert Foo2().bar == Foo().bar == 0


@mark.parametrize("field_type", [field, field_property])
@mark.parametrize(
    "overridden_args, bar, field_str",
    [(dict(inherit=True), 1, ""), (dict(default=1), 2, "bar=2")],
)
def test_override_field(field_type, overridden_args, bar, field_str):
    @dataclass
    class Foo:
        bar: int = field_type(default=0, repr=False)

    @dataclass
    class Foo2(Foo):
        bar: int = field_property(**overridden_args)

        @field_property(bar)
        def get_bar(self):
            return unwrap_property(self).bar + 1

    assert Foo().bar == 0
    assert Foo2().bar == bar
    assert str(Foo2()) == f"{Foo2.__qualname__}({field_str})"


@mark.parametrize(
    "accessor, operator, count",
    [
        ("getter", getattr, 1),
        ("setter", lambda obj, attr: setattr(obj, attr, 0), 2),
        ("deleter", delattr, 1),
    ],
)
def test_inherit_field_property_accessors(accessor, operator, count):
    @dataclass
    class Foo:
        bar: int = field_property()

    mock = Mock()
    delattr(mock, FSET_ATTRIBUTE)

    @dataclass
    class Foo2(Foo):
        bar: int = field_property()

        getattr(field_property(bar), accessor)(mock)

    operator(Foo2(0), "bar")
    assert mock.call_count == count


def test_inherit_setter_doesn_t_chain_default_handling():
    setter = Mock()
    delattr(setter, FSET_ATTRIBUTE)

    @dataclass
    class WithDefault:
        default: int = field_property(default=0, repr=False)
        field_property(default).setter(setter)

    with_default = WithDefault()
    setter.assert_called_with(with_default, 0)

    @dataclass
    class Inherited(WithDefault):
        default: int = field_property(default=0, repr=False)

    assert getattr(Inherited.default.fset, FSET_ATTRIBUTE) is setter


def test_invalid_field_property():
    with raises(ValueError, match=f"Invalid field property {None}"):
        field_property(None)


def test_frozen_dataclass():
    @dataclass(frozen=True)
    class Foo:
        bar: int = field_property()

    foo = Foo(0)
    assert foo.__dict__ == {"_bar": 0}
    assert foo.bar == 0
    with raises(FrozenInstanceError):
        foo.bar = 1
    with raises(FrozenInstanceError):
        del foo.bar


def test_read_only():
    @dataclass
    class Foo:
        bar: int = field_property(init=False, raw=True)

        @field_property(bar)
        def get_bar(self) -> int:
            return 0

    assert Foo().bar == 0
    with raises(AttributeError):
        Foo().bar = 1
