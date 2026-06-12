      SUBROUTINE MISALIGNED
C     A 1-byte LOGICAL*1 pushes the DOUBLE PRECISION onto an odd
C     offset  -> basic alignment warning
      CHARACTER FLAG
      DOUBLE PRECISION VALUE
      COMMON /MIX/ FLAG, VALUE
      VALUE = 0.0D0
      END
