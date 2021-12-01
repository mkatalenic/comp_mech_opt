#!/usr/bin/env python3
'''
Postavljanje input datoteke za Calculix
Pokretanje Calculixa
'''
from datetime import datetime as dt

import re
import subprocess
import os 
import shutil

import numpy as np

import geometry_creation as gc

def create_calculix_inputfile(used_mesh,
                              filename: str = dt.now().strftime('mesh_%d_%M_%H%M%S'),
                              nonlin: bool = True) -> str:
    '''Metoda ispisa mreže u input_file'''

    os.mkdir(filename)

    with open(filename + '/' + filename + '.inp', 'w', encoding='ascii') as ccx_input_file:

        # Definicija čvorova
        ccx_input_file.write('*node, nset=nall\n')
        ccx_input_file.writelines(
            [f'{i + 1}, {np.array2string(row, separator=",")[1:-1]}\n'
             for i, row in enumerate(used_mesh.node_array)]
        )

        # Definicija greda
        elset_name_list: list[str] = []
        for index, segbeam in enumerate(used_mesh.segmentedbeam_array):
            elset_name = f'b_{index}'
            elset_name_list.append(elset_name)
            ccx_input_file.write(f'*element, type=b32, elset={elset_name}\n')
            ccx_input_file.writelines(
                [f'{i + 1 + index * used_mesh.segmentedbeam_divisions}, \
                {np.array2string(row + 1, separator=",")[1:-1]}\n'
                 for i, row in enumerate(segbeam)]
            )
        ccx_input_file.write('*elset, elset=elall\n')
        ccx_input_file.writelines([f'{name},\n' for name in elset_name_list])

        # Materials
        ccx_input_file.write('*material, name=mesh_material\n' +\
                             '*elastic, type=iso\n' + \
                             f'{used_mesh.material}'[1:-1] + '\n')

        # Postavljanje poprečnog presjeka greda
        for elset_name, width in zip(elset_name_list, used_mesh.segmentedbeam_width_array):
            ccx_input_file.write(f'*beam section,elset={elset_name},' +
                                 'material=mesh_material,section=rect\n')
            ccx_input_file.write(f'{used_mesh.segmentedbeam_height}, {width}\n' +
                                 '0.d0,0.d0,1.d0\n')

        # Definiranje 2D slučaja
        ccx_input_file.write('*boundary\n')
        ccx_input_file.writelines([f'{i + 1}, 3,5\n' \
                                   for i in range(used_mesh.last_added_node_index + 1)])

        # Postavljanje oslonaca
        ccx_input_file.write('*boundary\n')
        ccx_input_file.writelines([f'{node_id+1}, {sup_type}\n' \
                                   for (node_id,sup_type) in used_mesh.boundary_list])


        # Postavljanje sila
        if nonlin:
            ccx_input_file.write('*step, nlgeom\n*static\n*cload\n')
        else:
            ccx_input_file.write('*step\n*static\n*cload\n')
        for (node_id, force) in used_mesh.force_list:
            out_x_force_string = f'{node_id+1}, 1, {force[0]}\n'
            out_y_force_string = f'{node_id+1}, 2, {force[1]}\n'
            if force[1] != 0.:
                ccx_input_file.write(out_y_force_string)
            if force[0] != 0.:
                ccx_input_file.write(out_x_force_string)


        ccx_input_file.write('*el print, elset=elall\ns\n')
        ccx_input_file.write('*node file, output=2d, nset=nall\nu\n')
        ccx_input_file.write('*el file, elset=elall\ns,noe\n')
        ccx_input_file.write('*el print, nset=nall\nevol\n')
        ccx_input_file.write('*end step')

    return filename

def output_string_formatter(output_string: str):
    '''Vraća potrebni format ispisa'''
    exponentials = re.split('E', output_string)[1:]
    output_numbers = re.split('E...',output_string)[:-1]

    output_numbers = [float(num) * 10**float(exp[:3])
                      for num,exp in zip(output_numbers,exponentials)]

    return output_numbers

def read_node_displacement_and_stress(filename: str):
    '''Čitanje pomaka pojedinih čvorova mreže'''

    with open(filename + '.frd', 'r', encoding='utf8') as results_file:
        displacement_list = []
        stress_list = []

        in_disp_section = False
        in_stress_section = False
        for line in results_file:

            if line[5:].startswith('DISP'):
                in_disp_section = True

            if line[5:].startswith('STRESS'):
                in_stress_section = True

            if line.startswith(' -3'):
                in_disp_section = False
                in_stress_section = False

            if in_disp_section:
                displacement_list.append(output_string_formatter(line.strip()[12:]))

            if in_stress_section:
                stress_list.append(output_string_formatter(line.strip()[12:]))

    stress_array = np.array(stress_list[7:])
    displacement_array = np.array(displacement_list[5:])

    return displacement_array, stress_array

def run_ccx(filename: str,
            del_dir: bool = False):
    '''Pokretanje rješavaća, output su disp i stress'''
    os.chdir(filename)
    subprocess.run(['ccx', filename.strip(".inp")], check=True)
    disp, stress = read_node_displacement_and_stress(filename)
    os.chdir('..')

    if del_dir:
        shutil.rmtree(filename)

    return disp, stress

if __name__=='__main__':
    max_x = 1.52
    max_y = 3.24
    my_mesh = gc.SimpleMeshCreator(max_x, max_y, (3,3), 'fd')

    # my_mesh = gc.ReadGMSH

    # my_mesh.make_boundary((0,0), 1)
    # my_mesh.make_boundary((0,0), 2)

    my_mesh.make_boundary((max_x,0), 1)
    my_mesh.make_boundary((max_x,0), 2)

    my_mesh.make_boundary((max_x,max_y), 1)
    my_mesh.make_boundary((max_x,max_y), 2)

    my_mesh.make_boundary((0,max_y), 1)
    my_mesh.make_boundary((0,max_y), 2)

    my_mesh.make_force((max_x/2, 0), (0, 1000))
    my_mesh.make_force((0, max_y/3), (1500, 1000))

    my_mesh.material = (1e5, 0.29)

    my_mesh.segmentedbeam_height = 0.5
    my_mesh.segmentedbeam_initial_width = 0.5

    my_mesh.set_width_array(my_mesh.segmentedbeam_initial_width)

    current_mesh_filename = create_calculix_inputfile(my_mesh)

    run_ccx(current_mesh_filename, del_dir=False)
