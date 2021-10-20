#!/usr/bin/env python3

'''Definiranje geometrije mreže'''

import numpy as np
import numpy.typing as npt

class Mesh:

    '''
    Definiranje objekta mreže koji sprema podatke o mreži.
    Sadrži metode kreacije mreže.
    '''

    segmentedbeam_divisions: int = 4

    # Definiranje array-a u koji se spremaju koordinate čvorova
    node_array                 = np.empty(shape=(0,2),
                                          dtype=np.float64)

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
