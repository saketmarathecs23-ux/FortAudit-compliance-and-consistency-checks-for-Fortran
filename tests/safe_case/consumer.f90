      SUBROUTINE CONSUMER
C     Identical declaration of /SHARED/  -> SAFE, no diagnostics
      REAL X(50)
      INTEGER N
      COMMON /SHARED/ X, N
      SAVE /SHARED/
      PRINT *, X(1), N
      END
