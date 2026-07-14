subroutine grid_extra
   ! Third file: matches grid_mod.f90's REAL nodes layout exactly
   ! -> confirms grid_use.f90 is the outlier among three declarations
   implicit none
   real :: nodes(100)
   integer :: ncount
   common /meshdata/ nodes, ncount
   ncount = ncount + 1
end subroutine
