#!/usr/bin/env python3

'''
Mesh creation definitions
'''

import numpy as np
import numpy.typing as npt

class Mesh:

    '''
    Meta class defining neaded subclass charactersitics
    Contains:
    - Mesh object variables
    - Mesh creation methods
    - Node fetching methods
    - Boundary definitions
    - Force definitions


    ---------------------------------------------------------
    -------------------Variable definition-------------------
    ---------------------------------------------------------
    '''

    # defined as a tuple
    # (Module of elasticity, Poisson number)
    material: tuple

    # Beam division
    # Convergence testing
    segmentedbeam_divisions: int = 4

    # Node arrays
    # Contains all mesh nodes
    node_array          = np.empty(shape=(0,2),
                                   dtype=np.float64)

    # Contains only main nodes
    main_node_array     = np.empty(shape=(0),
                                   dtype=int)

    # Contains outer nodes
    outer_node_array    = np.empty(shape=(0),
                                   dtype=int)

    # Counts current node indices
    last_added_node_index: int = -1

    # Array that contains all segmentbeams (Beams connecting main nodes)
    segmentedbeam_array        = np.empty(shape=(0,
                                                 segmentedbeam_divisions,
                                                 3),
                                          dtype=int)

    # Array containing widths of all segmentbeams
    segmentedbeam_width_array = np.empty(shape=(0),
                                         dtype=float)

    # The height of the 2D beam construction
    segmentedbeam_height: float

    # Lists containing mesh boundaries and external forces
    boundary_list: list[tuple[int, int]] = []
    force_list: list[tuple[int, npt.NDArray]] = []

    '''
    ---------------------------------------------------------
    -------------------Node fetching methods-----------------
    ---------------------------------------------------------
    '''

    def fetch_near_main_node_index(self,
                                   coords: npt.ArrayLike) -> int:
        '''Fetches node index based on near coordinates'''

        coords = np.array(coords)
        closest_node_index = np.argmin(
            np.sqrt(
                np.sum(
                    np.square(
                        self.node_array[self.main_node_array] \
                        - np.repeat(coords.reshape((1,2)), np.size(self.main_node_array), axis=0)
                    ), axis=1
                )
            ), axis = 0
        )
        return closest_node_index

    def node_id_or_fetch_node(self,
                              node_def) -> int:

        '''
        Either forward given id or fetch the nearest node
        Checks the instance.
        '''
        if  isinstance(node_def, int):
            node_id = node_def
        else:
            node_id = self.fetch_near_main_node_index(node_def)
        return node_id

    '''
    ---------------------------------------------------------
    -------------------Creation methods----------------------
    ---------------------------------------------------------
    '''

    def create_node(self,
                    coords: npt.ArrayLike):
        '''
        Node creation method.
        Created nodes are added to the self.node_array.
        '''
        tmp_node_array = np.array(coords).reshape(1,2)
        self.node_array = np.append(self.node_array,
                                    tmp_node_array,
                                    axis=0)
        self.last_added_node_index += 1

    def create_main_node(self,
                         coords: npt.ArrayLike):
        '''
        Simoultanious node creation
        and
        addition to self.main_node_array
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
        Segmentedbeam creation.

        Consists of multiple beams.
        Segbeam consisting of only one beam contains 3 nodes
        (Calculix beam creation requires 3 node definition).
        Added to segmentbeam_array.
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

    '''
    ---------------------------------------------------------
    -----------Boundary creation methods---------------------
    ---------------------------------------------------------
    '''

    def make_boundary(self,
                      node_def,
                      boundary_type: int,
                      removable=True):

        '''
        Boundary definition based on boundary type:
        - 1 => x - translation
        - 2 => y - translation
        - 3 => z - rotation
        '''

        node_id = self.fetch_near_main_node_index(node_def)

        if boundary_type in [1,2,3]:
            if boundary_type == 3:
                boundary_type = 6
            self.boundary_list.append((node_id, boundary_type, removable))
        else:
            raise ValueError

    '''
    ---------------------------------------------------------
    --------------Force creation methods---------------------
    ---------------------------------------------------------
    '''

    def make_force(self,
                   node_def,
                   force_vec: npt.ArrayLike):

        '''
            Force definition based on given node and
            (x_force, y_force) vector
        '''

        node_id = self.node_id_or_fetch_node(node_def)
        force_vec = np.array(force_vec)

        self.force_list.append((node_id, force_vec))

    '''
    ---------------------------------------------------------
    --------------Width definition method--------------------
    ---------------------------------------------------------
    '''

    minimal_segmentedbeam_width: float

    current_segmentedbeams = np.array([])

    def set_width_array(self,
                        input_width):
        '''
        Width definition based on the instance of given args
        '''

        if isinstance(input_width, float):
            self.segmentedbeam_width_array = np.ones(np.shape(self.segmentedbeam_array)[0]) * input_width

        else:
            if np.size(input_width) == np.shape(self.segmentedbeam_array)[0]:

                beams_qued_for_removal = self.segmentedbeam_array[input_width < self.minimal_segmentedbeam_width]
                proposed_beams_left    = self.segmentedbeam_array[input_width >= self.minimal_segmentedbeam_width]
                self.segmentedbeam_width_array = input_width[input_width >= self.minimal_segmentedbeam_width]

                removed_main_nodes, removed_main_nodes_count = np.unique(
                    beams_qued_for_removal[:, [0, -1], [0, -1]],
                    return_counts=True
                )

                _, main_nodes_count = np.unique(
                    self.segmentedbeam_array[:, [0, -1], [0, -1]],
                    return_counts = True
                )

                # Lonely node constraint
                # A main node cannot have only one beam conected to it

                if 1 in main_nodes_count[removed_main_nodes] - removed_main_nodes_count:
                    raise ValueError('Lonely node alert!')

                # Force removal constraint
                # Raises an error if it tries to remove a beam containing force definition

                if np.size(
                        np.intersect1d(
                            proposed_beams_left,
                            np.array([node_id for node_id, _ in self.force_list])
                        )
                ) == 0:
                    raise ValueError('Trying to remove a force!')

                # Boundary removal constraint
                # Raises an error if it tries to remove most bounderies

                # Can't remove unremovable boundaries
                unremovable_boundary = np.unique(
                    np.array(
                        [node_id for node_id,_,removable in self.boundary_list if removable is False]
                    )
                )

                if np.intersect1d(
                        unremovable_boundary,
                        proposed_beams_left) == 0:
                    raise ValueError('Trying to remove an unremovable boundary!')

                explicit_boundary = np.array(
                    [[node_id, bound_def]  for node_id, bound_def, _ in self.boundary_list]
                )

                bd_left_in_proposed = np.intersect1d(
                    np.unique(explicit_boundary[:,0]),
                    proposed_beams_left
                )

                # If only one boundary is left
                if np.size(bd_left_in_proposed) == 1 and\
                   not np.isin(explicit_boundary[:,1][explicit_boundary[:,0] == int(bd_left_in_proposed)],
                           [1,2,6]).all():
                    raise ValueError('Too many boundaries removed!')

                # TODO If only two boundaries are left
                if np.size(bd_left_in_proposed) < 2:
                    raise ValueError('Too many boundaries removed!!')

                self.current_segmentedbeams = proposed_beams_left

            else:
                raise ValueError('Wrong array size!')


class SimpleMeshCreator(Mesh):

    '''
    A simple, automated mesh creaton based on given:
    - x dimension
    - y dimension
    - number of divisions (x_div, y_div)
    - support definitions
    '''

    def __init__(self,
                 length: float,
                 height: float,
                 divisions: tuple[int, int],
                 support_definition: str = None):
        '''
        Initialization
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
