      SUBROUTINE THIRDREADER
C     Third file: /STATE/ declared as LOGICAL  -> a third distinct
C     type punning on the same block, on top of reader.f90/writer.f90
      LOGICAL VALUE
      COMMON /STATE/ VALUE
      PRINT *, VALUE
      END
