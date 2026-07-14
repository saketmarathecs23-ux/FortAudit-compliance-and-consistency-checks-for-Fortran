      SUBROUTINE THIRDMOD
C     Third file: /DATA/ declared as DOUBLE PRECISION(50) = 400 bytes
C     Same size as physics.f90 (400 bytes) but different type
C     -> proves the check must compare ALL files, not just a pair
      DOUBLE PRECISION VALS(50)
      COMMON /DATA/ VALS
      VALS(1) = 1.0D0
      END
