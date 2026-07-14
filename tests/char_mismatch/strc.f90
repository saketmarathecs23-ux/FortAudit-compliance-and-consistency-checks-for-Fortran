      SUBROUTINE STRC
C     Third file: CHARACTER*32 -> a third distinct size for /IDENT/,
C     in addition to the 8-byte and 16-byte declarations
      CHARACTER*32 NAME
      COMMON /IDENT/ NAME
      PRINT *, NAME
      END
