#!/usr/bin/env python3

import random
import pickle
import matplotlib.pyplot as plt

import numpy as np

import calculix_manipulation as cm

# plt.style.use('dark_background')

# Importing mesh and width_history
cs = open('case_setup.pkl', 'rb')
my_mesh = pickle.load(cs)
cs.close()

with open('width_history','rb') as width_history_file:
    width_history = np.load(width_history_file, allow_pickle=True)

# Crtanje
my_figure = plt.figure()
ax = my_figure.add_subplot(1,1,1)
ax.set_aspect('equal')

zeljena_konfiguracija_za_prikaz = 611
my_mesh.set_width_array(width_history[zeljena_konfiguracija_za_prikaz])

# Prijevod konstrukcije u Calculix input
current_mesh_filename = cm.create_calculix_inputfile(my_mesh,
                                                   filename=f'probni_{random.randrange(2000,5000)}',
                                                   nonlin=True)
# Pokretanje Calculixa
displacement, stress = cm.run_ccx(current_mesh_filename)

index_of_change = np.unique(my_mesh.current_segmentedbeams)


'''
Potrebno iskomentirati + displacement[index] za potrebe prikaza same ne deformirane konstrukcije
'''
for index, change_index in enumerate(index_of_change):
    my_mesh.node_array[change_index] = my_mesh.node_array[change_index] + displacement[index]
selected_width = my_mesh.segmentedbeam_width_array
max_width = my_mesh.segmentedbeam_height

for segbeam, segbeam_width in zip(my_mesh.segmentedbeam_array,
                                  selected_width):
    if segbeam_width>my_mesh.minimal_segmentedbeam_width:
        _, idx = np.unique(segbeam, return_index=True)
        nodes_per_segbeam = np.reshape(segbeam, -1)[np.sort(idx)]

        ax.plot(my_mesh.node_array[nodes_per_segbeam][:,0],
                my_mesh.node_array[nodes_per_segbeam][:,1],
                '--',
                color = 'blue',
                lw = 1,
                zorder = 0)


bd_list = my_mesh.boundary_array

for node in my_mesh.main_node_array:
    if node in bd_list[:,0]:
        DOF_to_print = str(bd_list[bd_list[:,0]==node][:,1])[1:-1]

        ax.scatter(my_mesh.node_array[node][0],
                   my_mesh.node_array[node][1],
                   s = 200,
                   color = 'green',
                   marker = f'${DOF_to_print}$',
                   zorder = 1)
    else:
        ax.scatter(my_mesh.node_array[node][0],
                   my_mesh.node_array[node][1],
                   color = 'green',
                   marker = 'o',
                   zorder = 1)

for force in my_mesh.force_array:
    ax.annotate(f'{np.sqrt(np.sum(force[1:-1]**2)):.1E}N',
                xy=my_mesh.node_array[int(force[0])],
                xytext=(-0.25, 0.5),
                arrowprops=dict(arrowstyle="-|>"))

for init_disp in my_mesh.init_disp_array:
    ax.arrow(my_mesh.node_array[int(init_disp[0])][0],
             my_mesh.node_array[int(init_disp[0])][1],
             init_disp[1],
             init_disp[2],
             width = 0.1,
             color = 'red',
             zorder = 0
             )

plt.savefig('primjer_mesh.jpg', dpi=150)
