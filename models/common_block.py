"""Data models for COMMON block analysis."""

from dataclasses import dataclass, field
from typing import List


# Approximate byte sizes for common Fortran intrinsic types.
TYPE_SIZES = {
    "INTEGER": 4,
    "REAL": 4,
    "DOUBLE PRECISION": 8,
    "DOUBLEPRECISION": 8,
    "COMPLEX": 8,
    "LOGICAL": 4,
    "CHARACTER": 1,
}

# Natural alignment (bytes) used for the basic alignment check.
TYPE_ALIGNMENT = {
    "INTEGER": 4,
    "REAL": 4,
    "DOUBLE PRECISION": 8,
    "DOUBLEPRECISION": 8,
    "COMPLEX": 8,
    "LOGICAL": 4,
    "CHARACTER": 1,
}


@dataclass
class Variable:
    """A single variable inside a COMMON block declaration."""

    name: str
    type: str = "UNKNOWN"
    elements: int = 1          # array length (1 for scalars)
    char_len: int = 1          # CHARACTER(len=N)

    @property
    def element_size(self) -> int:
        base = TYPE_SIZES.get(self.type, 4)
        if self.type == "CHARACTER":
            base = self.char_len
        return base

    @property
    def size(self) -> int:
        return self.element_size * self.elements

    @property
    def alignment(self) -> int:
        return TYPE_ALIGNMENT.get(self.type, 4)

    def signature(self) -> str:
        if self.elements > 1:
            return f"{self.type} {self.name}({self.elements})"
        return f"{self.type} {self.name}"


@dataclass
class EquivalenceGroup:
    """An EQUIVALENCE statement group: variables forced to share storage."""

    members: List[Variable] = field(default_factory=list)
    line: int = 0

    def types(self):
        return {v.type for v in self.members}

    def is_type_punned(self) -> bool:
        return len(self.types()) > 1


@dataclass
class CommonDeclaration:
    """One COMMON block declaration as found in a single file."""

    block_name: str
    file: str
    line: int
    variables: List[Variable] = field(default_factory=list)
    saved: bool = False        # SAVE /block/ present in this file
    # EQUIVALENCE groups in this file that touch a variable of this block.
    equivalences: List[EquivalenceGroup] = field(default_factory=list)

    @property
    def total_size(self) -> int:
        return sum(v.size for v in self.variables)

    def layout(self):
        """Yield (offset, variable) tuples for the block layout."""
        offset = 0
        for v in self.variables:
            yield offset, v
            offset += v.size
