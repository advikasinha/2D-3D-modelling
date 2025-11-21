from ansys.mapdl.core import launch_mapdl

nmodes = 10
# start MAPDL
mapdl = launch_mapdl()
print(mapdl)

mapdl.prep7()
mapdl.mp("EX", 1, 2.1e11)
mapdl.mp("PRXY", 1, 0.3)
mapdl.mp("DENS", 1, 7800)

mapdl.k(1)
mapdl.k(2, 10)
mapdl.l(1, 2)
mapdl.lplot()

mapdl.et(1, "BEAM188")
mapdl.sectype(1, "BEAM", "RECT")
mapdl.secoffset("CENT")
mapdl.secdata(2, 1)

# Mesh the line
mapdl.type(1)
mapdl.esize(1)
mapdl.lesize("ALL")
mapdl.lmesh("ALL")
mapdl.eplot()
mapdl.finish()

mapdl.solution()  # Entering the solution processor.
mapdl.nsel("S", "LOC", "X", "0")
mapdl.d("ALL", "ALL")
mapdl.allsel()
mapdl.nplot(plot_bc=True, nnum=True)

mapdl.antype("MODAL")
mapdl.modopt("LANB", nmodes, 0, 200)
mapdl.solve()
mapdl.finish()

mapdl.post1()
output = mapdl.set("LIST")
print(output)

result = mapdl.result

mode2plot = 2
normalizeDisplacement = 1 / result.nodal_displacement(mode2plot - 1)[1].max()

result.plot_nodal_displacement(
    mode2plot,
    show_displacement=True,
    displacement_factor=normalizeDisplacement,
    n_colors=10,
)

result.animate_nodal_displacement(
    mode2plot,
    loop=False,
    add_text=False,
    n_frames=100,
    displacement_factor=normalizeDisplacement,
    show_axes=False,
    background="w",
    movie_filename="animation.gif",
    off_screen=True,
)

mapdl.finish()
mapdl.exit()