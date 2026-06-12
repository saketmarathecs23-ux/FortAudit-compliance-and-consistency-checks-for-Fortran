"""Polished compiler-style diagnostic output."""

import os
from typing import Dict, List

from models.common_block import CommonDeclaration
from validator.checks import (
    Diagnostic, SEVERITY_ERROR, SEVERITY_WARNING, SEVERITY_INFO,
)


class C:
    """ANSI color codes (disabled automatically when not a TTY)."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    MAGENTA = "\033[95m"
    GREY = "\033[90m"

    @classmethod
    def disable(cls):
        for attr in dir(cls):
            if attr.isupper():
                setattr(cls, attr, "")


def _enable_colors():
    if os.environ.get("NO_COLOR") or not _supports_color():
        C.disable()


def _supports_color():
    if os.name == "nt":
        # Modern Windows Terminal / VS Code support ANSI; enable virtual terminal.
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    import sys
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


SEV_STYLE = {
    SEVERITY_ERROR: lambda: f"{C.RED}{C.BOLD}",
    SEVERITY_WARNING: lambda: f"{C.YELLOW}{C.BOLD}",
    SEVERITY_INFO: lambda: f"{C.CYAN}",
}


def _rel(path):
    try:
        return os.path.relpath(path)
    except ValueError:
        return path


def print_header(num_files: int, num_blocks: int):
    _enable_colors()
    line = "=" * 52
    print(f"{C.CYAN}{line}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  FORTRAN COMMON BLOCK SAFETY ANALYZER{C.RESET}")
    print(f"{C.CYAN}{line}{C.RESET}")
    print()
    print(f"  {C.BOLD}Scanning:{C.RESET} {num_files} files")
    print(f"  {C.BOLD}COMMON blocks detected:{C.RESET} {num_blocks}")
    print()


def _declaration_view(d: CommonDeclaration) -> str:
    parts = []
    for v in d.variables:
        parts.append(v.signature())
    decl = ", ".join(parts)
    return decl


def print_diagnostic(diag: Diagnostic):
    style = SEV_STYLE.get(diag.severity, lambda: "")()
    print(f"{style}[{diag.severity}]{C.RESET} "
          f"{C.BOLD}COMMON block /{diag.block_name}/{C.RESET} — {diag.title}")
    print()

    shown = []
    for d in diag.declarations:
        if d in shown:
            continue
        shown.append(d)
        print(f"  {C.GREY}File:{C.RESET} {C.MAGENTA}{_rel(d.file)}{C.RESET}"
              f"{C.GREY}:{d.line}{C.RESET}")
        print(f"    COMMON /{diag.block_name}/ {_declaration_view(d)}")
        print(f"    {C.DIM}Size: {d.total_size} bytes"
              f"{'  (SAVE)' if d.saved else ''}{C.RESET}")
        for grp in d.equivalences:
            members = " <=> ".join(m.signature() for m in grp.members)
            print(f"    {C.DIM}EQUIVALENCE ({members}){C.RESET}")
        print()

    print(f"  {C.BOLD}Issue:{C.RESET}")
    for chunk in _wrap(diag.detail):
        print(f"    {chunk}")
    print()
    print(f"  {C.BOLD}{C.GREEN}Suggested Fix:{C.RESET} "
          f"Replace COMMON block with a MODULE")
    print(f"  {C.DIM}{'-' * 50}{C.RESET}")
    print()


def print_migration(block_name: str, decl: CommonDeclaration):
    print(f"  {C.BOLD}{C.GREEN}Suggested modernization for /{block_name}/:{C.RESET}")
    print()
    print(f"  {C.GREEN}MODULE {block_name.capitalize()}Data{C.RESET}")
    print(f"  {C.GREEN}  IMPLICIT NONE{C.RESET}")
    for v in decl.variables:
        if v.elements > 1:
            print(f"  {C.GREEN}  {v.type} :: {v.name}({v.elements}){C.RESET}")
        else:
            print(f"  {C.GREEN}  {v.type} :: {v.name}{C.RESET}")
    print(f"  {C.GREEN}END MODULE {block_name.capitalize()}Data{C.RESET}")
    print()


def print_summary(stats: Dict[str, int]):
    line = "=" * 52
    print(f"{C.CYAN}{line}{C.RESET}")
    print(f"{C.BOLD}  SUMMARY{C.RESET}")
    print(f"{C.CYAN}{line}{C.RESET}")
    print(f"  Files scanned........ {stats['files']}")
    print(f"  COMMON blocks........ {stats['blocks']}")
    print(f"  {C.RED}Errors............... {stats['errors']}{C.RESET}")
    print(f"  {C.YELLOW}Warnings............. {stats['warnings']}{C.RESET}")
    print(f"  {C.CYAN}Info................. {stats['info']}{C.RESET}")
    print()
    if stats['errors'] == 0 and stats['warnings'] == 0:
        print(f"  {C.GREEN}{C.BOLD}✓ No unsafe COMMON block usage detected.{C.RESET}")
    else:
        print(f"  {C.RED}{C.BOLD}✗ Unsafe COMMON block usage detected — "
              f"migration to MODULEs recommended.{C.RESET}")
    print()


def _wrap(text, width=72):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out
