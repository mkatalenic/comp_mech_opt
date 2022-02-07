#!/usr/bin/env python

'''Crtanje geometrije, za sad samo proba'''

import matplotlib.pyplot as plt

import numpy as np
import numpy.typing as npt

import geometry_creation as gc
import calculix_manipulation as cm

plt.style.use('dark_background')

if __name__=='__main__':

    max_x = 2
    max_y = 1
    my_mesh = gc.SimpleMeshCreator(max_x, max_y, (3,2), 'x')

    my_mesh.segmentedbeam_initial_width = 1e-2
    my_mesh.set_width_array(my_mesh.segmentedbeam_initial_width)

    my_figure = plt.figure()
    ax = my_figure.add_subplot(1,1,1)
    ax.set_aspect('equal')

    '''Crtanje greda'''
    for segbeam, segbeam_width in zip(my_mesh.segmentedbeam_array,
                                      my_mesh.segmentedbeam_width_array):

        _, idx = np.unique(segbeam, return_index=True)
        nodes_per_segbeam = np.reshape(segbeam, -1)[np.sort(idx)]

        ax.plot(my_mesh.node_array[nodes_per_segbeam][:,0],
                my_mesh.node_array[nodes_per_segbeam][:,1],
                '--',
                color = 'blue',
                lw = 1,
                zorder = 0)

    my_mesh.make_boundary((max_x,0), 1)
    my_mesh.make_boundary((max_x,0), 2)

    for node in my_mesh.fetch_nodes_in_area((-0.001, max_y), (max_x, max_y)):
        my_mesh.make_boundary(node, 1)
        my_mesh.make_boundary(node, 2)

    # my_mesh.make_boundary((max_x,max_y), 1)
    # my_mesh.make_boundary((max_x,max_y), 2)

    # my_mesh.make_boundary((0,max_y), 1)
    # my_mesh.make_boundary((0,max_y), 2)
    #
    '''Crtanje boundarya'''
    bd_list = np.array(my_mesh.boundary_list)
    for node in my_mesh.main_node_array:
        if node in bd_list[:,0]:
            DOF_to_print = str(bd_list[bd_list[:,0]==node][:,1])[1:-1]

            ax.scatter(my_mesh.node_array[node][0],
                       my_mesh.node_array[node][1],
                       s = 200,
                       color = 'yellow',
                       marker = f'${DOF_to_print}$',
                       zorder = 1)
        else:
            ax.scatter(my_mesh.node_array[node][0],
                       my_mesh.node_array[node][1],
                       color = 'yellow',
                       marker = 'o',
                       zorder = 1)

    '''Crtanje sila'''
    # my_mesh.make_force((0.5, 0), (1,1))
    # for force in my_mesh.force_list:
    #     ax.annotate(f'{np.sqrt(np.sum(force[1]**2)):.1E}N',
    #                 xy=my_mesh.node_array[force[0]],
    #                 xytext=(-0.25, 0.5),
    #                 arrowprops=dict(arrowstyle="-|>"))

    #     print(force[1])

    plt.show()

'''

    # my_mesh.make_force((max_x/2, 0), (0,1))

    my_mesh.material = (1e7, 0.3)

    my_mesh.segmentedbeam_height = 1e-2
'''
