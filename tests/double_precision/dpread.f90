      SUBROUTINE DPREAD
C     REAL array = 4 * 10 = 40 bytes  -> size + type mismatch on /GEOM/
      REAL COORD(10)
      COMMON /GEOM/ COORD
      PRINT *, COORD(1)
      END
