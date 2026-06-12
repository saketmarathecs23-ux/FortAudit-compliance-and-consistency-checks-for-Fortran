      SUBROUTINE PACKER
C     EQUIVALENCE forces a REAL and an INTEGER to share storage
C     inside /BUF/  -> storage-association type punning
      REAL RBUF(4)
      INTEGER IBUF(4)
      COMMON /BUF/ RBUF
      EQUIVALENCE (RBUF, IBUF)
      RBUF(1) = 1.0
      END
