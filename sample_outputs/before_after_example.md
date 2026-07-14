# Before / After Example — `/DATA/` COMMON Block

## BEFORE (unsafe — from `tests/size_mismatch/`)

**physics.f90**
```fortran
      SUBROUTINE PHYSICS
C     Declares /DATA/ as 100 REALs = 400 bytes
      REAL TEMP(100)
      COMMON /DATA/ TEMP
      TEMP(1) = 273.15
      END
```

**solver.f90**
```fortran
      SUBROUTINE SOLVER
C     Declares /DATA/ as 200 INTEGERs = 800 bytes  -> SIZE MISMATCH
      INTEGER GRID(200)
      COMMON /DATA/ GRID
      GRID(1) = 0
      END
```

Both files compile individually with zero errors. Linked together, `PHYSICS`
and `SOLVER` share the same 400-byte memory region but disagree on its size
and type — `SOLVER` writes 800 bytes of `INTEGER` into a region `PHYSICS`
believes is 400 bytes of `REAL`. This is exactly what the analyzer flags:

```
[ERROR] COMMON block /DATA/ — Inconsistent memory layout detected
  File: tests/size_mismatch/physics.f90:4   Size: 400 bytes
  File: tests/size_mismatch/solver.f90:4    Size: 800 bytes
  Issue: Size mismatch: 400 bytes vs 800 bytes.
```

---

## AFTER (safe — MODULE-based migration)

**data_mod.f90** (new file, replaces the `COMMON` block)
```fortran
MODULE DataData
  IMPLICIT NONE
  REAL :: TEMP(100)
END MODULE DataData
```

**physics.f90** (rewritten)
```fortran
      SUBROUTINE PHYSICS
      USE DataData
      IMPLICIT NONE
      TEMP(1) = 273.15
      END
```

**solver.f90** (rewritten — must now use the SAME variable, not its own)
```fortran
      SUBROUTINE SOLVER
      USE DataData
      IMPLICIT NONE
      TEMP(1) = 0.0
      END
```

## Why this is verifiably safe

1. **Single source of truth.** `TEMP`'s type and size are declared exactly
   once, in `data_mod.f90`. Every subroutine that `USE`s the module sees the
   identical layout — there is no second declaration that could drift.
2. **The original bug becomes a compile error, not silent corruption.**
   If `solver.f90` still tried to declare its own `INTEGER GRID(200)` and use
   it as if it aliased `/DATA/`, that variable simply wouldn't exist in the
   module — `gfortran` would fail with an undefined-symbol / type error at
   compile time instead of corrupting memory at run time.
3. **Compile it yourself to confirm:**
   ```bash
   gfortran -c data_mod.f90
   gfortran -c physics.f90 solver.f90
   gfortran data_mod.o physics.o solver.o -o test
   ```
   A clean compile + link proves the module is well-formed and that both
   subroutines now agree on `/DATA/`'s layout by construction.
