import matplotlib.pyplot as plt
import numpy as np

from ansys.mapdl.core import launch_mapdl

mapdl = launch_mapdl(loglevel="ERROR")

mapdl.clear()
mapdl.prep7()

# Material properties-- 1020 steel in imperial
mapdl.units("BIN")  # U.S. Customary system using inches (in, lbf*s2/in, s, °F).
mapdl.mp("EX", 1, 30023280.0)
mapdl.mp("NUXY", 1, 0.290000000)
mapdl.mp("ALPX", 1, 8.388888889e-06)
mapdl.mp("DENS", 1, 7.346344000e-04)
mapdl.mp("KXX", 1, 6.252196000e-04)
mapdl.mp("C", 1, 38.6334760)

# use a thermal element type
mapdl.et(1, "SOLID70")

mapdl.block(0, 5, 0, 1, 0, 1)
mapdl.lesize("ALL", 0.2, layer1=1)

mapdl.mshape(0, "3D")
mapdl.mshkey(1)
mapdl.vmesh(1)
mapdl.eplot()

mapdl.run("/SOLU")
mapdl.antype(4)  # transient analysis
mapdl.trnopt("FULL")  # full transient analysis
mapdl.kbc(0)  # ramp loads up and down

# Time stepping
end_time = 1500
mapdl.time(end_time)  # end time for load step
mapdl.autots("ON")  # use automatic time stepping


# setup where the subset time is 10 seconds, time
mapdl.deltim(10, 2, 25)  # substep size (seconds)
#                          -- minimum value shorter than smallest
#                            time change in the table arrays below

# Create a table of convection times and coefficients and transfer it to MAPDL
my_conv = np.array(
    [
        [0, 0.001],  # start time
        [120, 0.001],  # end of first "flat" zone
        [130, 0.005],  # ramps up in 10 seconds
        [700, 0.005],  # end of second "flat zone
        [710, 0.002],  # ramps down in 10 seconds
        [end_time, 0.002],
    ]
)  # end of third "flat" zone
mapdl.load_table("my_conv", my_conv, "TIME")


# Create a table of bulk temperatures for a given time and transfer to MAPDL
my_bulk = np.array(
    [
        [0, 100],  # start time
        [120, 100],  # end of first "flat" zone
        [500, 300],  # ramps up in 380 seconds
        [700, 300],  # hold temperature for 200 seconds
        [900, 75],  # temperature ramps down for 200 seconds
        [end_time, 75],
    ]
)  # end of second "flat" zone
mapdl.load_table("my_bulk", my_bulk, "TIME")

# Force transient solve to include the times within the conv and bulk arrays
# my_tres = np.unique(np.vstack((my_bulk[:, 0], my_conv[:, 0])))[0]  # same as
mapdl.parameters["my_tsres"] = [120, 130, 500, 700, 710, 900, end_time]
mapdl.tsres("%my_tsres%")

mapdl.outres("ERASE")
mapdl.outres("ALL", "ALL")

mapdl.eqslv("SPARSE")  # use sparse solver
mapdl.tunif(75)  # force uniform starting temperature (otherwise zero)

# apply the convective load (convection coefficient plus bulk temperature)
# use "%" around table array names
mapdl.sfa(6, 1, "CONV", "%my_conv%", " %my_bulk%")

# solve
mapdl.solve()

mapdl.post1()

# get the temperature of the 30th result set
mapdl.set(1, 30)
temp = mapdl.post_processing.nodal_temperature()

# Load this result into the underlying VTK grid
grid = mapdl.mesh._grid
grid["temperature"] = temp

# generate a single horizontal slice slice along the XY plane
single_slice = grid.slice(normal=[0, 0, 1], origin=[0, 0, 0.5])
single_slice.plot(scalars="temperature")

# get the temperature of a different result set
mapdl.set(1, 120)
temp = mapdl.post_processing.nodal_temperature()

# Load this result into the underlying VTK grid
grid = mapdl.mesh._grid
grid["temperature"] = temp

# generate a single horizontal slice slice along the XY plane
slices = grid.slice_along_axis(7, "y")
slices.plot(scalars="temperature", lighting=False, show_edges=True)

# for example, the temperature of Node 12 is can be retrieved simply with:
mapdl.get_value("node", 12, "TEMP")

# note that this is similar to # *GET, Par, NODE, N, Item1, IT1NUM, Item2, IT2NUM
# See the MAPDL reference for all the items you can obtain using *GET
nsets = mapdl.post_processing.nsets
node_temp = []
for i in range(1, 1 + nsets):
    mapdl.set(1, i)
    node_temp.append(mapdl.get_value("node", 12, "TEMP"))

# here are the first 10 temperatures
node_temp[:10]

# get the index of node 12 in MAPDL
idx = np.nonzero(mapdl.mesh.nnum == 12)[0][0]

# get the temperature at that index for each result
node_temp_from_post = []
for i in range(1, 1 + nsets):
    mapdl.set(1, i)
    node_temp_from_post.append(mapdl.post_processing.nodal_temperature()[idx])

# Again, the first 10 temperatures
node_temp_from_post[:10]

time_values = mapdl.post_processing.time_values
plt.plot(time_values, node_temp, label="Node 12")
plt.plot(my_bulk[:, 0], my_bulk[:, 1], ":", label="Input")
plt.legend()
plt.xlabel("Time (seconds)")
plt.ylabel(r"Temperature ($^\circ$F)")
plt.show()

mapdl.exit()