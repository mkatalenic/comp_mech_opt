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
my_mesh.move_node((max_x/2,max_y), (0, -0.5))

# Granična vrijednost debljine greda rešetke
my_mesh.minimal_segmentedbeam_width = 0.05

# Postavljanje početne debljine greda rešetke
my_mesh.set_width_array(my_mesh.segmentedbeam_initial_width)
my_mesh.write_beginning_state()

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
