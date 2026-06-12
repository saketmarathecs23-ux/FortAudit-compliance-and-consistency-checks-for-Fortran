#!/usr/bin/env python3
"""FORTRAN COMMON Block Memory Safety Analyzer.

Scans Fortran source files, reconstructs COMMON block layouts, and reports
unsafe cross-file usage (size/type/ordering/SAVE/alignment issues) with
compiler-style diagnostics and modernization advice.

Usage:
    python analyzer.py tests/
    python analyzer.py tests/size_mismatch/ tests/type_punning/
    python analyzer.py file1.f90 file2.f90
"""

import os
import sys
from collections import defaultdict

# Ensure UTF-8 output so box/check glyphs render on Windows consoles too.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from parser.fortran_parser import parse_file
from validator.checks import (
    analyze_block, SEVERITY_ERROR, SEVERITY_WARNING, SEVERITY_INFO,
)
from validator import reporter


FORTRAN_EXTS = (".f", ".f90", ".f77", ".for", ".f95")


def collect_files(paths):
    files = []
    for path in paths:
        if os.path.isdir(path):
            for root, _, names in os.walk(path):
                for name in names:
                    if name.lower().endswith(FORTRAN_EXTS):
                        files.append(os.path.join(root, name))
        elif os.path.isfile(path) and path.lower().endswith(FORTRAN_EXTS):
            files.append(path)
    return sorted(files)


def main(argv):
    if len(argv) < 2:
        print("usage: python analyzer.py <dir-or-files ...>")
        return 2

    files = collect_files(argv[1:])
    if not files:
        print("No Fortran (.f/.f90) files found in the given paths.")
        return 1

    # Build the global COMMON block database: name -> [declarations].
    database = defaultdict(list)
    for f in files:
        try:
            for decl in parse_file(f):
                database[decl.block_name].append(decl)
        except Exception as exc:  # keep the demo resilient
            print(f"  (skipped {f}: {exc})")

    reporter.print_header(len(files), len(database))

    stats = {"files": len(files), "blocks": len(database),
             "errors": 0, "warnings": 0, "info": 0}

    problem_blocks = []
    for block_name in sorted(database):
        decls = database[block_name]
        diagnostics = analyze_block(block_name, decls)
        if not diagnostics:
            continue
        problem_blocks.append((block_name, decls[0]))
        for diag in diagnostics:
            reporter.print_diagnostic(diag)
            if diag.severity == SEVERITY_ERROR:
                stats["errors"] += 1
            elif diag.severity == SEVERITY_WARNING:
                stats["warnings"] += 1
            else:
                stats["info"] += 1

    if problem_blocks:
        line = "=" * 52
        print(f"{reporter.C.CYAN}{line}{reporter.C.RESET}")
        print(f"{reporter.C.BOLD}  MIGRATION ADVISOR{reporter.C.RESET}")
        print(f"{reporter.C.CYAN}{line}{reporter.C.RESET}\n")
        for block_name, decl in problem_blocks:
            reporter.print_migration(block_name, decl)

    reporter.print_summary(stats)
    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
