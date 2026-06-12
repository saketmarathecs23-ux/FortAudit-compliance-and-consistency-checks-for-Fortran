"""Cross-file consistency checks for COMMON blocks."""

from dataclasses import dataclass
from typing import List

from models.common_block import CommonDeclaration


SEVERITY_ERROR = "ERROR"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFO"


@dataclass
class Diagnostic:
    severity: str
    block_name: str
    title: str
    detail: str
    declarations: List[CommonDeclaration]


def analyze_block(block_name: str, decls: List[CommonDeclaration]) -> List[Diagnostic]:
    """Run all checks for one COMMON block across its declarations."""
    diagnostics: List[Diagnostic] = []
    if len(decls) < 2:
        return diagnostics

    reference = decls[0]
    diagnostics += _check_size(block_name, decls, reference)
    diagnostics += _check_types(block_name, decls, reference)
    diagnostics += _check_ordering(block_name, decls, reference)
    diagnostics += _check_save(block_name, decls)
    diagnostics += _check_alignment(block_name, decls)
    diagnostics += _check_equivalence(block_name, decls)
    return diagnostics


def _check_size(block_name, decls, reference):
    out = []
    ref_size = reference.total_size
    for d in decls[1:]:
        if d.total_size != ref_size:
            out.append(Diagnostic(
                SEVERITY_ERROR, block_name,
                "Inconsistent memory layout detected",
                f"Size mismatch: {ref_size} bytes vs {d.total_size} bytes. "
                "Potential silent memory corruption across translation units.",
                [reference, d],
            ))
    return out


def _check_types(block_name, decls, reference):
    out = []
    for d in decls[1:]:
        for i, ref_var in enumerate(reference.variables):
            if i >= len(d.variables):
                break
            other = d.variables[i]
            if ref_var.type != other.type:
                out.append(Diagnostic(
                    SEVERITY_ERROR, block_name,
                    "Type mismatch / type punning",
                    f"Position {i + 1}: '{ref_var.name}' declared {ref_var.type} "
                    f"but '{other.name}' declared {other.type}. "
                    "Reinterpreting the same bytes as a different type is undefined behavior.",
                    [reference, d],
                ))
    return out


def _check_ordering(block_name, decls, reference):
    out = []
    ref_names = [v.name.upper() for v in reference.variables]
    for d in decls[1:]:
        other_names = [v.name.upper() for v in d.variables]
        if sorted(ref_names) == sorted(other_names) and ref_names != other_names:
            out.append(Diagnostic(
                SEVERITY_WARNING, block_name,
                "Variable ordering mismatch",
                f"Order {ref_names} vs {other_names}. Same names, different order — "
                "each file sees different data at the same offset.",
                [reference, d],
            ))
    return out


def _check_save(block_name, decls):
    saved = [d for d in decls if d.saved]
    if saved and len(saved) != len(decls):
        missing = [d for d in decls if not d.saved]
        return [Diagnostic(
            SEVERITY_WARNING, block_name,
            "SAVE inconsistency",
            f"SAVE /{block_name}/ present in {len(saved)} file(s) but missing in "
            f"{', '.join(d.file for d in missing)}. Lifetime of the block is inconsistent.",
            decls,
        )]
    return []


def _check_equivalence(block_name, decls):
    """Detect storage-association hazards introduced by EQUIVALENCE.

    Two flavors:
      1. Type punning *within* a file: EQUIVALENCE forces variables of
         different types to share storage in this COMMON block.
      2. Cross-file inconsistency: EQUIVALENCE touches the block in some
         files but not others, so the effective layout disagrees.
    """
    out = []

    # 1. Per-file EQUIVALENCE type punning.
    for d in decls:
        for grp in d.equivalences:
            if grp.is_type_punned():
                names = " <=> ".join(m.signature() for m in grp.members)
                types = ", ".join(sorted(grp.types()))
                out.append(Diagnostic(
                    SEVERITY_ERROR, block_name,
                    "EQUIVALENCE storage-association conflict",
                    f"In {d.file}: EQUIVALENCE ({names}) forces incompatible "
                    f"types ({types}) to share the same storage inside /{block_name}/. "
                    "Writing through one alias and reading the other is type punning.",
                    [d],
                ))

    # 2. Cross-file presence inconsistency.
    have_equiv = [d for d in decls if d.equivalences]
    if have_equiv and len(have_equiv) != len(decls):
        without = [d for d in decls if not d.equivalences]
        out.append(Diagnostic(
            SEVERITY_WARNING, block_name,
            "Inconsistent EQUIVALENCE association across files",
            f"EQUIVALENCE alters /{block_name}/ in "
            f"{', '.join(d.file for d in have_equiv)} but not in "
            f"{', '.join(d.file for d in without)}. The effective storage "
            "layout differs between translation units.",
            decls,
        ))
    return out


def _check_alignment(block_name, decls):
    out = []
    for d in decls:
        for offset, var in d.layout():
            if var.alignment > 1 and offset % var.alignment != 0:
                out.append(Diagnostic(
                    SEVERITY_INFO, block_name,
                    "Possible alignment issue",
                    f"In {d.file}: '{var.name}' ({var.type}) sits at offset {offset}, "
                    f"not a multiple of its {var.alignment}-byte alignment. "
                    "May cause padding differences or slow unaligned access.",
                    [d],
                ))
                break  # one note per declaration is enough for the demo
    return out
