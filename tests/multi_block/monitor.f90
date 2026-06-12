      SUBROUTINE MONITOR
C     /TUNING/ matches engine.f90 (safe), but /STATE2/ here is REAL
C     not INTEGER  -> type punning on /STATE2/ only
      REAL GAIN, BIAS
      REAL MODE
      COMMON /TUNING/ GAIN, BIAS
      COMMON /STATE2/ MODE
      PRINT *, MODE
      END
