      SUBROUTINE THIRDFILE
C     Third file: SAVE present, matching init.f90 but conflicting
C     with update.f90 -> confirms majority vs minority isn't assumed,
C     every file's SAVE status must be cross-checked
      INTEGER COUNTER
      COMMON /COUNTERS/ COUNTER
      SAVE /COUNTERS/
      COUNTER = COUNTER + 2
      END
