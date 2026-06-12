subroutine grid_query
   ! Mismatch: nodes declared as integer here -> type punning on /MESHDATA/
   implicit none
   integer :: nodes(100)
   integer :: ncount
   common /meshdata/ nodes, ncount
   print *, ncount
end subroutine
