"""Lightweight regex-based Fortran parser for COMMON block extraction.

This is intentionally NOT a full Fortran parser. It scans source lines for
type declarations, COMMON statements and SAVE statements, which is enough to
reconstruct COMMON block layouts for the safety analyzer.
"""

import re
from typing import Dict, List

from models.common_block import CommonDeclaration, EquivalenceGroup, Variable


# Recognised intrinsic type keywords (longest first so DOUBLE PRECISION wins).
TYPE_KEYWORDS = [
    "DOUBLE PRECISION",
    "DOUBLEPRECISION",
    "CHARACTER",
    "COMPLEX",
    "INTEGER",
    "LOGICAL",
    "REAL",
]

_COMMON_RE = re.compile(r"^\s*COMMON\s*/\s*(\w+)\s*/\s*(.+)$", re.IGNORECASE)
_SAVE_RE = re.compile(r"^\s*SAVE\s*/\s*(\w+)\s*/", re.IGNORECASE)
_EQUIV_RE = re.compile(r"^\s*EQUIVALENCE\s*(.+)$", re.IGNORECASE)
_EQUIV_GROUP_RE = re.compile(r"\(([^)]*)\)")
_CHAR_LEN_RE = re.compile(r"CHARACTER\s*(?:\(\s*LEN\s*=\s*(\d+)\s*\)|\*\s*(\d+))", re.IGNORECASE)


def _strip_comments(line: str) -> str:
    # Fixed-form comment markers in column 1.
    if line[:1] in ("C", "c", "*", "!"):
        return ""
    # Inline free-form comment.
    return line.split("!", 1)[0]


def _join_continuations(raw_lines: List[str]) -> List[tuple]:
    """Merge Fortran continuation lines, returning (line_number, text)."""
    merged = []
    for idx, raw in enumerate(raw_lines, start=1):
        text = _strip_comments(raw.rstrip("\n"))
        if not text.strip():
            continue
        # Free-form continuation: previous line ended with '&'.
        if merged and merged[-1][1].rstrip().endswith("&"):
            prev_line, prev_text = merged[-1]
            merged[-1] = (prev_line, prev_text.rstrip()[:-1] + " " + text.strip())
            continue
        # Fixed-form continuation: non-blank char in column 6.
        if len(raw) > 5 and raw[5] not in (" ", "0", "\t") and raw[:5].strip() == "" and merged:
            prev_line, prev_text = merged[-1]
            merged[-1] = (prev_line, prev_text.rstrip() + " " + text[6:].strip())
            continue
        merged.append((idx, text))
    return merged


def _parse_type_decls(lines: List[tuple]) -> Dict[str, Variable]:
    """Map declared variable name -> typed Variable template."""
    decls: Dict[str, Variable] = {}
    for _, text in lines:
        upper = text.upper().strip()
        matched_type = next((t for t in TYPE_KEYWORDS if upper.startswith(t)), None)
        if not matched_type:
            continue

        char_len = 1
        if matched_type == "CHARACTER":
            m = _CHAR_LEN_RE.search(text)
            if m:
                char_len = int(m.group(1) or m.group(2))

        # Strip the type keyword and any (len=..)/*N qualifier to get the var list.
        rest = re.sub(r"^\s*" + matched_type.replace(" ", r"\s+"),
                      "", text, flags=re.IGNORECASE)
        rest = re.sub(r"^\s*(\(\s*LEN\s*=\s*\d+\s*\)|\*\s*\d+)", "", rest, flags=re.IGNORECASE)
        rest = rest.lstrip(" :")

        for name, elems in _split_var_list(rest):
            decls[name.upper()] = Variable(name=name, type=matched_type,
                                           elements=elems, char_len=char_len)
    return decls


def _split_var_list(text: str):
    """Split 'A, B(100), C' into [(name, elements), ...] respecting parens."""
    items, depth, current = [], 0, ""
    for ch in text:
        if ch == "(":
            depth += 1
            current += ch
        elif ch == ")":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0:
            items.append(current)
            current = ""
        else:
            current += ch
    if current.strip():
        items.append(current)

    result = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        m = re.match(r"(\w+)\s*(?:\(([^)]*)\))?", item)
        if not m:
            continue
        name = m.group(1)
        elements = 1
        if m.group(2):
            elements = _dim_to_count(m.group(2))
        result.append((name, elements))
    return result


def _dim_to_count(dim: str) -> int:
    """Compute element count from a dimension spec like '100' or '2,3' or '0:9'."""
    total = 1
    for part in dim.split(","):
        part = part.strip()
        if ":" in part:
            lo, hi = part.split(":", 1)
            try:
                total *= (int(hi) - int(lo) + 1)
            except ValueError:
                pass
        else:
            try:
                total *= int(part)
            except ValueError:
                pass
    return total


def _resolve_variable(name: str, type_decls: Dict[str, Variable]) -> Variable:
    """Resolve a bare name to a typed Variable using declarations + implicit rules."""
    template = type_decls.get(name.upper())
    if template:
        return Variable(name=name, type=template.type,
                        elements=template.elements, char_len=template.char_len)
    implied = "INTEGER" if name[:1].upper() in "IJKLMN" else "REAL"
    return Variable(name=name, type=implied)


def _parse_equivalences(lines: List[tuple], type_decls: Dict[str, Variable]):
    """Extract EQUIVALENCE statements as resolved EquivalenceGroup objects."""
    groups = []
    for line_no, text in lines:
        m = _EQUIV_RE.match(text)
        if not m:
            continue
        for raw_group in _EQUIV_GROUP_RE.findall(m.group(1)):
            members = []
            for token in raw_group.split(","):
                token = token.strip()
                if not token:
                    continue
                # Strip any array subscript: A(2) -> A
                base = re.match(r"(\w+)", token)
                if base:
                    members.append(_resolve_variable(base.group(1), type_decls))
            if len(members) >= 2:
                groups.append(EquivalenceGroup(members=members, line=line_no))
    return groups


def parse_file(path: str) -> List[CommonDeclaration]:
    """Parse one Fortran file, returning all COMMON declarations it contains."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        raw_lines = fh.readlines()

    lines = _join_continuations(raw_lines)
    type_decls = _parse_type_decls(lines)

    saved_blocks = set()
    for _, text in lines:
        m = _SAVE_RE.match(text)
        if m:
            saved_blocks.add(m.group(1).upper())

    equivalence_groups = _parse_equivalences(lines, type_decls)

    declarations: List[CommonDeclaration] = []
    for line_no, text in lines:
        m = _COMMON_RE.match(text)
        if not m:
            continue
        block_name = m.group(1).upper()
        var_list = m.group(2)

        variables = []
        for name, elems in _split_var_list(var_list):
            template = type_decls.get(name.upper())
            if template:
                variables.append(Variable(name=name, type=template.type,
                                          elements=template.elements or elems,
                                          char_len=template.char_len))
            else:
                # Fortran implicit typing: I-N => INTEGER, else REAL.
                implied = "INTEGER" if name[0].upper() in "IJKLMN" else "REAL"
                variables.append(Variable(name=name, type=implied, elements=elems))

        # Attach EQUIVALENCE groups that touch any variable of this block.
        block_var_names = {v.name.upper() for v in variables}
        related_equivs = [
            g for g in equivalence_groups
            if any(mem.name.upper() in block_var_names for mem in g.members)
        ]

        declarations.append(CommonDeclaration(
            block_name=block_name,
            file=path,
            line=line_no,
            variables=variables,
            saved=block_name in saved_blocks,
            equivalences=related_equivs,
        ))
    return declarations
