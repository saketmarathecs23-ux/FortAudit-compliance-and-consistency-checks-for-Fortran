# FORTRAN COMMON Block Memory Safety Analyzer

A static analysis tool that scans multiple Fortran source files and detects
**unsafe COMMON block usage across files** — the classic source of silent
memory corruption in legacy Fortran codebases.

---

## 1. Problem Statement

Fortran `COMMON` blocks are a global, untyped shared-memory region. Every file
that declares a `COMMON` block must agree **byte-for-byte** on its layout — but
the compiler does **not** check this across files. Mismatches compile cleanly
and then corrupt memory at runtime.

This tool reconstructs the layout of each `COMMON` block in every file, builds
a global database, and reports any disagreement with polished, compiler-style
diagnostics.

## 2. Why COMMON Blocks Are Dangerous

```fortran
! physics.f90              ! solver.f90
REAL TEMP(100)             INTEGER GRID(200)
COMMON /DATA/ TEMP         COMMON /DATA/ GRID
```

Both files share the storage named `/DATA/`, but one sees 400 bytes of `REAL`
and the other 800 bytes of `INTEGER`. There is **no compiler error**. At
runtime the two routines read and write the same memory with different sizes
and types → silent corruption, undefined behavior, and bugs that only appear
under optimization or on a different platform.

Common failure modes this tool catches:

| Check | Example |
|-------|---------|
| **Size mismatch** | `REAL X(100)` vs `INTEGER X(200)` |
| **Type punning** | `REAL TEMP` vs `INTEGER TEMP` |
| **Ordering mismatch** | `COMMON /D/ A, B` vs `COMMON /D/ B, A` |
| **EQUIVALENCE conflict** | `EQUIVALENCE (RBUF, IBUF)` aliasing a `REAL` block as `INTEGER` |
| **SAVE inconsistency** | `SAVE /D/` in one file, missing in another |
| **Alignment** | a `DOUBLE PRECISION` landing on a non-8-byte offset |

## Deliverables Coverage

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | Multi-file COMMON collector + global database | ✅ [`analyzer.py`](analyzer.py) builds a `name → [declarations]` DB |
| 2 | Validator: size, type punning, alignment, EQUIVALENCE, SAVE | ✅ [`validator/checks.py`](validator/checks.py) |
| 3 | Test suite of 20+ multi-file programs | ✅ 22 files / 10 scenarios in [`tests/`](tests/) |
| 4 | Evaluation on a real legacy codebase | ✅ ODEPACK, see [`legacy_eval/`](legacy_eval/README.md) |
| 5 | Migration advisor (COMMON → MODULE) | ✅ printed per problem block |

## 3. Architecture Overview

```
project/
├── analyzer.py            # CLI entry point + orchestration
├── parser/
│   └── fortran_parser.py  # regex-based COMMON / type / SAVE extraction
├── validator/
│   ├── checks.py          # cross-file consistency checks -> Diagnostics
│   └── reporter.py        # colored, compiler-style output + migration advisor
├── models/
│   └── common_block.py    # Variable / CommonDeclaration data models + sizes
├── tests/                 # 22 files across 10 scenarios
│   ├── size_mismatch/        type_punning/      ordering_mismatch/
│   ├── save_mismatch/        equivalence_conflict/
│   ├── alignment_issue/      char_mismatch/     double_precision/
│   ├── multi_block/          freeform_case/     safe_case/
├── legacy_eval/           # evaluation on real ODEPACK source (deliverable #4)
│   ├── src/                  # downloaded Netlib .f files
│   └── README.md             # methodology + results
├── sample_outputs/
├── requirements.txt
└── README.md
```

**Pipeline:** `parse files → build global COMMON database → run checks per block
→ emit diagnostics + modernization advice → summary`.

The parser is deliberately lightweight (regex + simplified layout computation),
not a full compiler front-end — enough to convincingly demonstrate the concept.

## 4. How to Run

Requires **Python 3.7+**. No third-party dependencies.

```bash
# Scan an entire tree
python analyzer.py tests/

# Scan specific scenarios
python analyzer.py tests/size_mismatch/ tests/type_punning/

# Scan individual files
python analyzer.py a.f90 b.f90
```

Exit code is `1` when errors are found, `0` when clean — handy for CI.

## 5 & 6. Demo Examples / Sample Outputs

**Unsafe `/DATA/` block (size + type mismatch):**

```
[ERROR] COMMON block /DATA/ — Inconsistent memory layout detected

  File: tests/size_mismatch/physics.f90:4
    COMMON /DATA/ REAL TEMP(100)
    Size: 400 bytes

  File: tests/size_mismatch/solver.f90:4
    COMMON /DATA/ INTEGER GRID(200)
    Size: 800 bytes

  Issue:
    Size mismatch: 400 bytes vs 800 bytes. Potential silent memory
    corruption across translation units.

  Suggested Fix: Replace COMMON block with a MODULE
```

**Migration advisor:**

```
  Suggested modernization for /DATA/:

  MODULE DataData
    IMPLICIT NONE
    REAL :: TEMP(100)
  END MODULE DataData
```

A full run transcript is saved in [`sample_outputs/full_run.txt`](sample_outputs/full_run.txt).

## 7. Real-World Evaluation (ODEPACK)

Run on ~1.2 MB of real Netlib ODEPACK Fortran 77:

```
Files scanned ........ 3            Wall-clock ........... ~0.19 s
COMMON blocks ........ 6            Declarations ......... 74
Storage-association issues flagged . 113
```

Every flagged site is a genuine cross-unit `COMMON` coupling (full named layout
vs. flat `RLS(218), ILS(37)` array view in the save/restore routines). Full
methodology and transcript in [`legacy_eval/README.md`](legacy_eval/README.md).

## 8. Future Improvements

- Use a real Fortran front-end (Flang/LLVM) for exact layouts and full `EQUIVALENCE` offset math.
- Model compiler-specific padding/alignment rules per target ABI.
- Auto-generate and apply the `MODULE` refactor (rewrite call sites).
- Support `BLOCK DATA`, `INCLUDE` files, and `DIMENSION` statements.
- JSON / SARIF output for CI dashboards and IDE integration.
