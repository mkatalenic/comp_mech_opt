#!/usr/bin/env python3
'''
Program koji pokreće Dash interface uz interaktivno pokretanje, kreaciju, dodavanje
'''

from datetime import datetime as dt
import numpy as np
import geometry_creation as gc

def create_calculix_inputfile(used_mesh,
                              file_name: str = dt.now().strftime('mesh_%d_%M_%H%M%S')) -> str:
    '''Metoda ispisa mreže u input_file'''


    with open(file_name + '.inp', 'w', encoding='ascii') as ccx_input_file:

        # Definicija čvorova
        ccx_input_file.write('*node, nset=all\n')
        ccx_input_file.writelines(
            [f'{i + 1}, {np.array2string(row, separator=",")[1:-1]}\n'
             for i, row in enumerate(used_mesh.node_array)]
        )

        # Definicija greda
        for index, segbeam in enumerate(used_mesh.segmentedbeam_array):
            ccx_input_file.write(f'*element, type=b32, elset=b_{index}\n')
            ccx_input_file.writelines(
                [f'{i + 1 + index * used_mesh.segmentedbeam_divisions}, \
                {np.array2string(row, separator=",")[1:-1]}\n'
                 for i, row in enumerate(segbeam)]
            )


        # Materials
        ccx_input_file.write('*material, name=mesh_material\n' +\
                             '*elastic, type=iso\n' + \
                             f'{used_mesh.material}'[1:-1] + '\n')

        # Definiranje 2D slučaja
        ccx_input_file.write('*boundary\n')
        ccx_input_file.writelines([f'{i + 1}, 1,4,5\n' for i in range(used_mesh.last_added_node_index + 1)])

    return file_name

def start_calculix_simulation(file_name: str):
    pass


if __name__=='__main__':
    my_mesh = gc.SimpleMeshCreator(10, 10, (10,10), 'x')

    current_mesh_filename = create_calculix_inputfile(my_mesh)
