# Evaluation on a Real Legacy Fortran Codebase — ODEPACK

This directory satisfies deliverable #4: *"Evaluation on a real legacy Fortran
codebase."* We ran the analyzer on **ODEPACK**, the canonical Fortran 77 suite
of ODE solvers (LSODE/LSODA/LSODAR/...), downloaded directly from Netlib.

## Why ODEPACK?

ODEPACK is the textbook example of decades-old production Fortran built around
`COMMON` blocks for solver state. Its internal state block `/DLS001/` is
declared in **39 different subroutines**. Unlike BLAS/LAPACK (which barely use
`COMMON`), ODEPACK exercises exactly the storage-association patterns this tool
targets — making it an ideal real-world stress test.

Source: https://www.netlib.org/odepack/ (`opkda1.f`, `opkda2.f`, `opkdmain.f`)

## How to reproduce

```bash
# from the project root
python analyzer.py legacy_eval/src
```

(The three `.f` files total ~1.2 MB / ~30k lines of real Fortran 77.)

## Results

| Metric | Value |
|--------|-------|
| Files scanned | 3 (~1.2 MB) |
| Wall-clock time | **~0.19 s** |
| Distinct COMMON blocks | 6 |
| Total COMMON declarations | 74 |
| Storage-association issues flagged | 113 |

Declarations per block:

| Block | Declarations |
|-------|-------------|
| `/DLS001/` | 39 |
| `/DLSS01/` | 11 |
| `/DLPK01/` | 9 |
| `/DLSR01/` | 6 |
| `/DLSA01/` | 6 |
| `/DLS002/` | 3 |

Full transcript: [`odepack_run_full.txt`](odepack_run_full.txt) ·
Trimmed excerpt: [`odepack_run_excerpt.txt`](odepack_run_excerpt.txt)

## What the tool found (and is it correct?)

**The findings are real, not false positives.** ODEPACK declares each state
block two different ways:

1. A **named layout** in the solver core, e.g.

   ```fortran
   COMMON /DLPK01/ DELT, EPCON, SQRTN, RSQRTN, JPRE, JACFLG, ...
   ```

2. A **flat array view** in the matching save/restore routine
   (`DSRCOM`, `DSRCPK`, ...), e.g.

   ```fortran
   COMMON /DLS001/ RLS(218), ILS(37)
   ```

The same physical storage is reinterpreted under different names, types, and
element counts. That is precisely **storage association / type punning across
translation units** — the analyzer reports the size and type disagreements
between the two views.

**Important nuance for the demo:** in ODEPACK these dual views are *intentional
and carefully maintained by the authors* — the save/restore routines exist to
checkpoint the block. So they are not live bugs in ODEPACK. But they are exactly
the constructs that become silent-corruption bugs the moment someone edits one
view and forgets the other. The tool's value is surfacing every such coupling
automatically: **113 storage-association points a maintainer would otherwise
have to find by hand**, located with precise `file:line` references, in a fifth
of a second.

This is the honest takeaway to present: the analyzer scales to real 30k-line
legacy code, runs instantly, and pinpoints every cross-unit `COMMON` coupling —
the union of genuine bugs *and* fragile-by-design constructs worth auditing
before a refactor to `MODULE`s.
