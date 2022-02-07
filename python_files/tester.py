#!/usr/bin/env python3

import numpy as np
import random

import geometry_creation as gc
import calculix_manipulation as cm

# Kreacija jednostavne mreže
max_x = 10
max_y = 10
my_mesh = gc.SimpleMeshCreator(max_x, max_y, (2,2), 'fd')

# Materijalni parametri mreže
my_mesh.material = (1e5, 0.29)

# Geometrijski parametri mreže
my_mesh.segmentedbeam_height = 0.5
my_mesh.segmentedbeam_initial_width = 0.5

# Zadavanje oslonaca konstrukcije
my_mesh.make_boundary((0,0), 1)
my_mesh.make_boundary((0,0), 2)

my_mesh.make_boundary((max_x,0), 1)
my_mesh.make_boundary((max_x,0), 2)

my_mesh.make_boundary((max_x,max_y), 1)
my_mesh.make_boundary((max_x,max_y), 2)

my_mesh.make_boundary((0,max_y), 1)
my_mesh.make_boundary((0,max_y), 2)

# Zadavanje opterećenja konstrukcije
# my_mesh.make_force((max_x/2, 0), (0, 1000))

# Zadavanje početnih pomaka konstrukcije
my_mesh.move_node((max_x/2,0), (0, 0.5))
# my_mesh.move_node((max_x/2,max_y), (0, -0.5))

# Granična vrijednost debljine greda rešetke
my_mesh.minimal_segmentedbeam_width = 0.05

# Postavljanje početne debljine greda rešetke
my_mesh.set_width_array(my_mesh.segmentedbeam_initial_width)
my_mesh.write_beginning_state()

'''
for i in range(20):
    my_mesh.set_width_array(np.random.random(np.size(my_mesh.segmentedbeam_width_array)) * my_mesh.segmentedbeam_initial_width)
    my_mesh.save_width_array()

    # Prijevod konstrukcije u Calculix input
    current_mesh_filename = cm.create_calculix_inputfile(my_mesh,
                                                         filename=f'probni_{random.randrange(2000,5000)}',
                                                         nonlin=True)
    # Pokretanje Calculixa
    displacement, stress = cm.run_ccx(current_mesh_filename)

    # Uzima se samo posljednji step
    displacement_last = displacement[-np.size(np.unique(my_mesh.current_segmentedbeams)):]
    stress_last = stress[-np.size(np.unique(my_mesh.current_segmentedbeams)):]
'''

'''Proba optimizacije'''
def max_translation_error_y_axsis(given_width_array,
                                  unique_srt=None):

    try:
        my_mesh.set_width_array(given_width_array)
        opt_area = my_mesh.mechanism_area
        truth_array = my_mesh.truth_array
        width = my_mesh.segmentedbeam_width_array

        current_mesh_filename = cm.create_calculix_inputfile(my_mesh, filename=unique_srt, nonlin=True)

        disp, _ = cm.run_ccx(current_mesh_filename, del_dir=True)

        displacement_of_node_in_interest = disp[my_mesh.fetch_near_main_node_index([max_x/2, max_y])]
        y_error = abs(float(1/displacement_of_node_in_interest[0]))
        x_error = abs(float(displacement_of_node_in_interest[1])) - 0.005

        obj_error = y_error
        obj_area  = opt_area
        constraint = x_error

        my_mesh.save_width_array(width)

        return obj_error, obj_area, constraint
    except:
        return np.nan, np.nan, np.nan



# Iitialize the algorithm
from indago import PSO
optimizer = PSO()

# Opt. var. settings
optimizer.dimensions = np.size(my_mesh.segmentedbeam_width_array)
optimizer.lb = np.zeros_like(my_mesh.segmentedbeam_width_array)
optimizer.ub = my_mesh.segmentedbeam_width_array

# Evaluation function
optimizer.evaluation_function = max_translation_error_y_axsis

# Objectives and constraints
optimizer.objectives = 2
optimizer.objective_labels = ['Max y translation', 'Construction area(mass)']
optimizer.objective_weights = [0.6,0.4]
optimizer.constraints = 1
optimizer.constraint_labels = ['Max x translation']

optimizer.safe_evaluation = False
optimizer.eval_fail_behavior = 'ignore'
# optimizer.eval_retry_attempts = 3

optimizer.monitoring = 'basic'

optimizer.forward_unique_str = True
result = optimizer.optimize()
optimizer.results.plot_convergence()
