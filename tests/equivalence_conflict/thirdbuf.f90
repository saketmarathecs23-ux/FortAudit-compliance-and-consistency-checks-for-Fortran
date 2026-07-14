      SUBROUTINE THIRDBUF
C     Third file: uses /BUF/ as REAL with no EQUIVALENCE, same as
C     unpacker.f90 -> confirms packer.f90 is the outlier among 3 files
      REAL RBUF(4)
      COMMON /BUF/ RBUF
      RBUF(2) = 2.0
      END
