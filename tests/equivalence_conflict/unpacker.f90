      SUBROUTINE UNPACKER
C     This file uses /BUF/ WITHOUT the EQUIVALENCE  -> cross-file
C     EQUIVALENCE inconsistency in addition to the punning above
      REAL RBUF(4)
      COMMON /BUF/ RBUF
      PRINT *, RBUF(1)
      END
