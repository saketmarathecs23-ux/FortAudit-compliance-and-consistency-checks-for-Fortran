      SUBROUTINE DPTHIRD
C     Third file: matches dpwrite.f90's DOUBLE PRECISION layout exactly
C     -> confirms dpread.f90 is the outlier among three declarations
      DOUBLE PRECISION COORD(10)
      COMMON /GEOM/ COORD
      COORD(2) = 2.0D0
      END
