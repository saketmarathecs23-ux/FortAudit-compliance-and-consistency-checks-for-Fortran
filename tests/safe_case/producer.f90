      SUBROUTINE PRODUCER
C     Consistent declaration of /SHARED/
      REAL X(50)
      INTEGER N
      COMMON /SHARED/ X, N
      SAVE /SHARED/
      N = 50
      END
