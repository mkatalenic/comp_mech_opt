#!/usr/bin/env python3

from os.path import exists
from indago import PSO
import numpy as np

import geometry_creation as gc
import calculix_manipulation as cm

def save_result(*args,
        mesh):

    '''Spremanje rezultata optimizacije i zadanih debljina greda'''

    array_to_save = np.array([args])

    if exists('./optimization_results'):
        with open('optimization_results', 'rb') as opt_res_file:
            saved_optim_res = np.reshape(
                np.load(opt_res_file, allow_pickle=True),
                (-1,len(args)))

        out_res = np.append(saved_optim_res,
                            array_to_save,
                            axis=0)
    else:
        out_res = array_to_save

    mesh.save_width_array(mesh.segmentedbeam_width_array)

    with open('optimization_results', 'wb') as optim_res_file:
        np.save(optim_res_file,
                out_res,
                allow_pickle=True)

# Kreacija jednostavne mreže
max_x = 10
max_y = 5
my_mesh = gc.SimpleMeshCreator(max_x, max_y, (4,2), 'x')

# Materijalni parametri mreže
my_mesh.material = (1e5, 0.29)

# Geometrijski parametri mreže
my_mesh.segmentedbeam_height = 0.5
my_mesh.segmentedbeam_initial_width = 0.5

# Zadavanje oslonaca konstrukcije
for node in my_mesh.fetch_nodes_in_area((4, -0.1),(7.7, 0.1)):
    my_mesh.make_boundary(node, 2, removable=0)

my_mesh.make_boundary((2.5,0), 1, removable=0)
my_mesh.make_boundary((2.5,0), 2, removable=0)

# Zadavanje početnih pomaka konstrukcije
my_mesh.move_node((0,max_y), (0, -0.5))

# Granična vrijednost debljine greda rešetke
my_mesh.minimal_segmentedbeam_width = 0.05

# Postavljanje početne debljine greda rešetke
my_mesh.set_width_array(my_mesh.segmentedbeam_initial_width)
my_mesh.write_beginning_state()

def max_translation_error_y_axsis(given_width_array_percentage,
                                  unique_str=None):

    '''Funkcija cilja'''

    current_mesh_filename = unique_str

    try:
        my_mesh.set_width_array(given_width_array_percentage * my_mesh.segmentedbeam_initial_width)
        opt_area = my_mesh.mechanism_area

        current_mesh_filename = cm.create_calculix_inputfile(my_mesh, filename=unique_str, nonlin=True)

        disp, _ = cm.run_ccx(current_mesh_filename, del_dir=True, no_threads=1)

        disp_last = disp[-np.size(np.unique(my_mesh.current_segmentedbeams)):]

        displacement_of_node_in_interest = disp_last[my_mesh.fetch_near_main_node_index([max_x, max_y/2])]
        y_error = 1/float(displacement_of_node_in_interest[1])
        x_error = abs(float(displacement_of_node_in_interest[0])) - 0.005
        negativan_pomak_const = float(displacement_of_node_in_interest[1])

        obj_error = y_error
        obj_area  = opt_area
        constraint = x_error
        constraint_2 = negativan_pomak_const

        save_result(obj_error, obj_area, constraint, mesh = my_mesh)

        return obj_error, obj_area, constraint, constraint_2

    except:
        return np.nan, np.nan, np.nan, np.nan



# Iitialize the algorithm
optimizer = PSO()

# Opt. var. settings
optimizer.dimensions = np.size(my_mesh.segmentedbeam_width_array)
optimizer.lb = np.zeros_like(my_mesh.segmentedbeam_width_array)
optimizer.ub = np.ones_like(my_mesh.segmentedbeam_width_array)

# Evaluation function
optimizer.evaluation_function = max_translation_error_y_axsis

# Objectives and constraints
optimizer.objectives = 2
optimizer.objective_labels = ['Max y translation', 'Construction area(mass)']
optimizer.objective_weights = [0.6,0.4]
optimizer.constraints = 2
optimizer.constraint_labels = ['Max x translation', 'Negative y translation']

optimizer.params['inertia'] = 0.8
optimizer.params['cognitive_rate'] = 1.
optimizer.params['social_rate'] = 1.0

optimizer.safe_evaluation = False
optimizer.eval_fail_behavior = 'ignore'
# optimizer.eval_retry_attempts = 3

optimizer.number_of_processes = 48
optimizer.params['swarm_size'] = 48

optimizer.iterations = 4000

optimizer.forward_unique_str = True
result = optimizer.optimize()
