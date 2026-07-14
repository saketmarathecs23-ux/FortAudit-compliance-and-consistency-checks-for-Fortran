      SUBROUTINE THIRDUSER
C     Third file: identical declaration of /SHARED/ -> still SAFE,
C     confirms consistency holds across all three files, not just two
      REAL X(50)
      INTEGER N
      COMMON /SHARED/ X, N
      SAVE /SHARED/
      PRINT *, X(2), N
      END
