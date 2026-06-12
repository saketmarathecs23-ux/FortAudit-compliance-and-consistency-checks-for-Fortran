      SUBROUTINE SOLVER
C     Declares /DATA/ as 200 INTEGERs = 800 bytes  -> SIZE MISMATCH
      INTEGER GRID(200)
      COMMON /DATA/ GRID
      GRID(1) = 0
      END
