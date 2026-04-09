from typing import Protocol, TypeVar

_T_co = TypeVar("_T_co", covariant=True)
_T_contra = TypeVar("_T_contra", contravariant=True)


# fmt: off
# Vendored from
# https://github.com/python/typeshed/blob/7c8e82fe483a40ec4cb0a2505cfdb0f3e7cc81d9/stdlib/_typeshed/__init__.pyi#L239-L253
class SupportsRead(Protocol[_T_co]):
    def read(self, length: int = ..., /) -> _T_co: ...

class SupportsWrite(Protocol[_T_contra]):
    def write(self, s: _T_contra, /) -> object: ...
# fmt: on
