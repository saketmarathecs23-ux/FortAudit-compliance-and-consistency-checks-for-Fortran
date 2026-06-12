      SUBROUTINE STRB
C     CHARACTER*16 here = 16 bytes  -> size mismatch on /IDENT/
      CHARACTER*16 NAME
      COMMON /IDENT/ NAME
      PRINT *, NAME
      END
