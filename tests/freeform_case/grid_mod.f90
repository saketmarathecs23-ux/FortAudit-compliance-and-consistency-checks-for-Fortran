subroutine grid_setup
   ! Free-form Fortran 90 with a continuation line
   implicit none
   real :: nodes(100)
   integer :: ncount
   common /meshdata/ nodes, &
                     ncount
   ncount = 100
end subroutine
