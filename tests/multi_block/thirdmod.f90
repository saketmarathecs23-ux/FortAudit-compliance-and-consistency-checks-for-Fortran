      SUBROUTINE THIRDMOD
C     Third file: /TUNING/ still consistent, /STATE2/ here is
C     INTEGER again (matches engine.f90) -> confirms monitor.f90's
C     REAL MODE is the odd one out across three files, not just two
      REAL GAIN, BIAS
      INTEGER MODE
      COMMON /TUNING/ GAIN, BIAS
      COMMON /STATE2/ MODE
      MODE = MODE + 1
      END
