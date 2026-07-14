      SUBROUTINE MODC
C     Third file: matches moduleA.f90's order (A then B) exactly.
C     Proves the tool isn't just diffing two files -- it must still
C     flag moduleB.f90 as the odd one out among three declarations.
      REAL A
      REAL B
      COMMON /PARAMS/ A, B
      A = 3.0
      B = 4.0
      END
