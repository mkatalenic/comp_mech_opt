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
            [f'{i}, {np.array2string(row, separator=",")[1:-1]}\n'
             for i, row in enumerate(used_mesh.node_array)]
        )

        # Definicija greda
        for index, segbeam in enumerate(used_mesh.segmentedbeam_array):
            ccx_input_file.write(f'*element, type=b32, elset=b_{index}\n')
            ccx_input_file.writelines(
                [f'{i + index * used_mesh.segmentedbeam_divisions}, \
                {np.array2string(row, separator=",")[1:-1]}\n'
                 for i, row in enumerate(segbeam)]
            )

        return file_name

if __name__=='__main__':
    my_mesh = gc.SimpleMeshCreator(10, 10, (2,2))

    current_mesh_filename = create_calculix_inputfile(my_mesh)
