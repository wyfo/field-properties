# field-properties
Properties for dataclass fields

## Example
```python
from dataclasses import dataclass

from field_properties import field_property, unwrap_property


@dataclass(frozen=True)
class Foo:
    bar: int = field_property(default=0)  # Same parameter than dataclasses.field

    @field_property(bar)  # Equivalent to @field_property(bar).getter
    def get_bar(self) -> int:
        # unwrap_property(self).bar is equivalent to self._bar
        # but it's type-checked and linter-friendly
        return unwrap_property(self).bar
    
    # When not declared, getter, setter and deleter are generated like the following:
    # @field_property(bar).setter
    # def set_bar(self, value: int):
    #     unwrap_property(self).bar = value


assert repr(Foo()) == repr(Foo(0)) == "Foo(bar=0)"
```

## How does it works?

When a dataclass field has a default value, this value is assigned as a class attribute. `field_property` use this mechanism and create a field with a property as default value. 

If a default value/factory is registered with `field_property`, the property setter will be called with it in `__init__`. 

## Default getter/setter/deleter

`field_property` generates default getter/setter/deleter as simple wrappers around an instance attribute whose name is the field name prefixed with an underscore `_`. `unwrap_property` allows accessing this attribute in a type-checked/linter-friendly way.

By the way, if all the getter/setter/deleter are declared (and thus not generated), the protected attribute will not be created.

## Overriding

Field properties can be overridden, but the dataclass field must be overridden too — this is because a new field must be created, as property is declared as its default value (see [previous section](#how-does-it-works)).

```python
from dataclasses import dataclass

from field_properties import field_property, unwrap_property


@dataclass
class Foo:
    bar: int = field_property(default=0)
    
    @field_property(bar)
    def get_bar(self):
        return unwrap_property(self).bar + 1

class Foo2(Foo):
    bar: int = field_property(default=0)  # field property must be overridden
    # field_property(inherit=True) is a shortcut to override a field
    # and reusing all it's arguments
    
    @field_property(bar)
    def get_bar(self):
        return unwrap_property(self).bar + 2
    

assert Foo() == 1
assert Foo2() == 2
```

In fact, because field is redeclared, it's also possible to override normal fields with a field property

```python
from dataclasses import dataclass

from field_properties import field_property


@dataclass
class Foo:
    bar: int = 0

class Foo2(Foo):
    bar: int = field_property(default=1)

assert Foo2() == 1
```

## Raw property

`field_property` comes with a default implementation for its getter/setter/deleter. This can be turned off with `raw=False` parameter. Here is an example of a read_only field:

```python
from dataclasses import dataclass
from field_properties import field_property

@dataclass
class Foo:
    bar: int = field_property(init=False, raw=True)

    @field_property(bar)
    def get_bar(self) -> int:
        return 0

assert Foo().bar == 0
assert str(Foo()) == "Foo(bar=0)"
try:
    Foo().bar = 1
except AttributeError:
    assert True
else:
    assert False
```

## [PEP 614](https://www.python.org/dev/peps/pep-0614/)

Decorator syntax `@field_property(bar).setter` is only valid in *Python 3.9*. Previous version can use the following hack:

```python
from dataclasses import dataclass

from field_properties import field_property


@dataclass
class Foo:
    bar: int = field_property()

    def set_bar(self, value: int):
        ...
    field_property(bar).setter(set_bar)
``` 