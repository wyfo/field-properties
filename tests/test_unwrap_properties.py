from dataclasses import dataclass

from pytest import raises

from field_properties import field_property, unwrap_property


@dataclass
class Foo:
    bar: int = field_property()

    def get_bar(self) -> int:
        return unwrap_property(self).bar

    def set_bar(self, value: int):
        unwrap_property(self).bar = value

    def del_bar(self):
        del unwrap_property(self).bar

    get_bar = field_property(bar).getter(get_bar)
    set_bar = field_property(bar).setter(set_bar)
    del_bar = field_property(bar).deleter(del_bar)


def test_unwrap_property():
    foo = Foo(0)
    assert foo.__dict__ == {"_bar": 0}
    assert foo.bar == 0
    del foo.bar
    assert foo.__dict__ == {}
    with raises(AttributeError):
        _ = foo.bar
