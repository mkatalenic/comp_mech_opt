#!/usr/bin/env python3

import numpy as np
# Geometry creation
import geometry_creation as gc

import calculix_manipulation as cm

'''
--------------------------------------------
--------------------TEST--------------------
--------------------------------------------
'''

max_x = 10
max_y = 10
my_mesh = gc.SimpleMeshCreator(max_x, max_y, (8,8), 'fd')

# my_mesh = gc.ReadGMSH

my_mesh.make_boundary((0,0), 1)
my_mesh.make_boundary((0,0), 2)

my_mesh.make_boundary((max_x,0), 1)
my_mesh.make_boundary((max_x,0), 2)

my_mesh.make_boundary((max_x,max_y), 1)
my_mesh.make_boundary((max_x,max_y), 2)

my_mesh.make_boundary((0,max_y), 1)
my_mesh.make_boundary((0,max_y), 2)

my_mesh.make_force((max_x/2, 0), (0, 1000))
# my_mesh.make_force((0, max_y/3), (1500, 1000))

my_mesh.material = (1e5, 0.29)

my_mesh.segmentedbeam_height = 0.5
my_mesh.segmentedbeam_initial_width = 0.5


rng = np.random.default_rng()
my_mesh.minimal_segmentedbeam_width = 0.05
my_mesh.set_width_array(my_mesh.segmentedbeam_initial_width)

my_mesh.write_to_history()
# Random vrijednosti
# NE SMIJE BITI ISTOVREMENO S OPTIMIZACIJOM UKLJUČENO
# my_mesh.set_width_array(np.random.rand(np.size(my_mesh.segmentedbeam_width_array)))

def max_translation_error_y_axis(given_width_array,
                                 unique_str=None):

    # my_mesh.segmentedbeam_width_array = given_width_array
    # print(np.size(given_width_array))
    # print(np.shape(my_mesh.segmentedbeam_width_array))
    my_mesh.set_width_array(given_width_array)
    current_mesh_filename = cm.create_calculix_inputfile(my_mesh, filename=unique_str ,nonlin=False)

    disp, _ = cm.run_ccx(current_mesh_filename, del_dir=True)

    y_error = float(1/ disp[my_mesh.fetch_near_main_node_index([max_x/2, max_y])][1])
    my_mesh.write_to_history(optim_res=np.array(y_error))
    # print(y_error)
    # x_error = float(disp[my_mesh.fetch_near_main_node_index([max_x/2, max_y])][0] - 0.0005)

    return y_error # , x_error

import indago

optimizer = indago.PSO()

optimizer.dimensions = np.size(my_mesh.segmentedbeam_width_array)
optimizer.lb = np.zeros(optimizer.dimensions)
optimizer.ub = np.ones(optimizer.dimensions) * 0.5

optimizer.evaluation_function = max_translation_error_y_axis
optimizer.safe_evaluation = True

optimizer.objectives = 1

# optimizer.monitoring = 'dashboard'

optimizer.forward_unique_str = True

result = optimizer.optimize()

print(result.f)
print(result.X)
