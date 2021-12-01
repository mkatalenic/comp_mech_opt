#!/usr/bin/env python3

'''Definiranje geometrije mreže'''

import numpy as np
import numpy.typing as npt

class Mesh:

    '''
    Definiranje objekta mreže koji sprema podatke o mreži.
    Sadrži metode kreacije mreže.
    '''

    material: tuple

    segmentedbeam_divisions: int = 4

    # Definiranje array-a u koji se spremaju koordinate čvorova
    node_array                 = np.empty(shape=(0,2),
                                          dtype=np.float64)

    main_node_array            = np.empty(shape=(0),
                                          dtype=int)

    outer_node_array           = np.empty(shape=(0),
                                          dtype=int)

    last_added_node_index: int = -1

    # Definiranje array-a u koji se spremaju pojedine grede
    segmentedbeam_array        = np.empty(shape=(0,
                                                 segmentedbeam_divisions,
                                                 3),
                                          dtype=int)

    def create_node(self,
                    coords: npt.ArrayLike):
        '''
        Kreacija novog čvora.
        Kreirani čvor sprema se u array.
        '''
        tmp_node_array = np.array(coords).reshape(1,2)
        self.node_array = np.append(self.node_array,
                                    tmp_node_array,
                                    axis=0)
        self.last_added_node_index += 1

    def create_main_node(self,
                         coords: npt.ArrayLike):
        '''
        Kreacija i zapisivanje glavnih čvorova
        '''
        self.create_node(coords)
        self.main_node_array = np.append(
            self.main_node_array,
            self.last_added_node_index
        )

    def create_segmentedbeam(self,
                             first_node: int,
                             last_node:  int):
        '''
        Postavljanje segmentirane grede koja se sastoji od više greda od 3 čvora.
        Kreirana segmentirana greda sprema se u segment_array.
        '''

        created_middle_nodes = np.linspace(self.node_array[first_node, :],
                                           self.node_array[last_node,  :],
                                           num = self.segmentedbeam_divisions*2 + 1,
                                           endpoint=True,
                                           axis=0)
        created_node_indexes: list[int] = []

        for node in created_middle_nodes[1:-1]:
            self.create_node(node)
            created_node_indexes.append(self.last_added_node_index)

        all_nodes_in_segbeam = [first_node] + created_node_indexes + [last_node]
        num_of_nodes = len(all_nodes_in_segbeam)

        segbeam_beams = np.array(
            [all_nodes_in_segbeam[index:index+3] for index in range(num_of_nodes)[:-2][::2]]
        )
        self.segmentedbeam_array = np.append(
            self.segmentedbeam_array,
            segbeam_beams.reshape((1,self.segmentedbeam_divisions,3)),
            axis=0
        )

class SimpleMeshCreator(Mesh):
    '''
    Jednostavna kreacija mreže na temelju početnih parametara
    '''

    def __init__(self,
                 length: float,
                 height: float,
                 divisions: tuple[int, int],
                 support_definition: str = None):
        '''
        Kreiranje jednostavne mreže
        '''
        for vertical_coord in np.linspace(0, height, divisions[1] + 1, endpoint=True):
            for horizontal_coord in np.linspace(0, length, divisions[0] + 1, endpoint=True):
                self.create_main_node((horizontal_coord, vertical_coord))

                if horizontal_coord in (0, length) or vertical_coord in (0, height):
                    self.outer_node_array = np.append(self.outer_node_array,
                                                      self.main_node_array[
                                                          self.last_added_node_index])

        for y_node in range(divisions[1] + 1):
            for x_node in range(divisions[0] + 1):
                current_node_id = x_node + y_node*(divisions[0] + 1)

                if x_node < divisions[0]:
                    self.create_segmentedbeam(current_node_id,
                                              current_node_id + 1)
                if y_node < divisions[1]:
                    self.create_segmentedbeam(current_node_id,
                                              current_node_id + (divisions[0] + 1))

                if support_definition == 'fd' and y_node < divisions[1] and x_node < divisions[0]:
                    self.create_segmentedbeam(current_node_id,
                                              current_node_id + 1 + (divisions[0] + 1))

                if support_definition == 'bd' and y_node < divisions[1] and x_node > 0:
                    self.create_segmentedbeam(current_node_id,
                                              current_node_id - 1 + (divisions[0] + 1))

                if support_definition == 'x' and y_node < divisions[1] and x_node < divisions[0]:
                    self.create_main_node(
                        np.average(
                            self.node_array[[current_node_id,
                                             current_node_id + 1 + (divisions[0] + 1)],:],
                            axis=0
                        )
                    )

                    created_mid_node_index = self.last_added_node_index

                    self.create_segmentedbeam(current_node_id,
                                              created_mid_node_index)
                    self.create_segmentedbeam(created_mid_node_index,
                                              current_node_id + 1 + (divisions[0] + 1))
                    self.create_segmentedbeam(current_node_id + (divisions[0] + 1),
                                              created_mid_node_index)
                    self.create_segmentedbeam(created_mid_node_index,
                                              current_node_id + 1)

    '''
   ----------------------------------------------------------------------------------------------------
    Definiranje početnih uvjeta mreže
   ----------------------------------------------------------------------------------------------------
    '''

    # Lista tuplova koji spremaju broj node_a i oblik oslonca
    boundary_list: list[tuple[int, int]] = []
    force_list: list[tuple[int, npt.NDArray]] = []

    def make_boundary(self,
                     node_def,
                     boundary_type: int):
        '''Definiranje novog oslonca na temelju tipa'''
        if  isinstance(node_def, int):
            node_id = node_def
        else:
            node_id = fetch_near_main_node_index(self,
                                                 node_def)

        if boundary_type in [1,2,3]:
            if boundary_type == 3:
                boundary_type = 6
            self.boundary_list.append((node_id, boundary_type))
        else:
            raise ValueError

    def make_force(self,
                   node_def,
                   force_vec: npt.ArrayLike):
        '''Definiranje nove sile na temelju vektorskog zapisa'''
        if  isinstance(node_def, int):
            node_id = node_def
        else:
            node_id = fetch_near_main_node_index(self,
                                                 node_def)

        force_vec = np.array(force_vec)
        self.force_list.append((node_id, force_vec))

    '''
    ----------------------------------------------------------------------------------------------------
    WIDTH DEFINITION
    ----------------------------------------------------------------------------------------------------
    '''
    segmentedbeam_width_array = np.empty(shape=(0),
                                         dtype=float)
    segmentedbeam_height: float

    def set_width_array(self,
                        width):
        '''Jednostavna definicija početnih uvjeta'''
        if isinstance(width, float):
            self.segmentedbeam_width_array = np.ones(np.shape(self.segmentedbeam_array)[0]) * width
        elif isinstance(width, npt.ArrayLike):
            if np.size(width) != np.shape(self.segmentedbeam_array)[0]:
                raise ValueError
            else:
                self.segmentedbeam_width_array = width


def fetch_near_main_node_index(selected_mesh: Mesh,
                               coords: npt.ArrayLike) -> int:
    '''Dohvaća točku u blizini definiranih koordinata'''

    coords = np.array(coords)
    closest_node_index = np.argmin(
        np.sqrt(
            np.sum(
                np.square(
                    selected_mesh.node_array[selected_mesh.main_node_array] \
                    - np.repeat(coords.reshape((1,2)), np.size(selected_mesh.main_node_array), axis=0)
                ), axis=1
            )
        ), axis = 0
    )

    return closest_node_index

if __name__ == '__main__':
    my_mesh = SimpleMeshCreator(2, 2, (10, 10), 'x')

    # print(my_mesh.main_node_array)
    # print(my_mesh.node_array)
    # print(my_mesh.segmentedbeam_array)
    # print(my_mesh.outer_node_array)
