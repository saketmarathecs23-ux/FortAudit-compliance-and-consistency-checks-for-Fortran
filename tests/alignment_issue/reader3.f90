      SUBROUTINE READER3
C     Third file: same misaligned layout as misaligned.f90/reader2.f90
C     -> confirms the alignment hazard is detected consistently
C     across every declaring file, not just a pair
      CHARACTER FLAG
      DOUBLE PRECISION VALUE
      COMMON /MIX/ FLAG, VALUE
      PRINT *, FLAG, VALUE
      END
