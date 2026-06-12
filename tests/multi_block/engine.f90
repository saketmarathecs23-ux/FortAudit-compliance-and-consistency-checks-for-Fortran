      SUBROUTINE ENGINE
C     Two COMMON blocks in one file; /TUNING/ is consistent,
C     /STATE2/ will clash with another file
      REAL GAIN, BIAS
      INTEGER MODE
      COMMON /TUNING/ GAIN, BIAS
      COMMON /STATE2/ MODE
      MODE = 1
      END
