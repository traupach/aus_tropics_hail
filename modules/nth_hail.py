import os 
import shutil
import numpy as np
import xarray

def sim_directory(lat, lon, year, month, day, hour, minute, sims_dir):
    return f'{sims_dir}/lat_{lat}_lon_{lon}_{year}-{month}-{day}_{hour:02}:{minute:02}'

def set_up_WRF(lat, lon, year, month, day, hour, minute, start_time, end_time, wrf_dir, sims_dir,
               mp_schemes={'P3-3M': 53, 'MY2': 9, 'NSSL': 17}):
    """
    Set up directories ready for WPS and WRF runs for a given event, including 
    updating namelist files.
    
    Arguments:
        lat, lon: Event location.
        year, month, day, hour, minute: Event time.
        start_time, end_time: Simulation start/end time as %Y-%m-%d_%H:%M:%S.
        wrf_dir: Directory with compiled WRF and basic namelist files.
        sims_dir: Output directory where simulations will be run.
        mp_schemes: Microphysics options to use; each will have a subdirectory under WRF.
    """

    sim_dir = f'{sims_dir}/lat_{lat}_lon_{lon}_{year}-{month}-{day}_{hour:02}:{minute:02}'
    if not os.path.exists(sim_dir):
        os.mkdir(sim_dir)
        
    # WPS setup. Link executables + data files, copy and update namelist.
    if not os.path.exists(f'{sim_dir}/WPS'):
        os.mkdir(f'{sim_dir}/WPS')
        os.system(f'ln -sf {wrf_dir}/WPS/Vtable {sim_dir}/WPS/Vtable')
        os.system(f'ln -sf {wrf_dir}/WPS/geogrid {sim_dir}/WPS/')
        os.system(f'ln -sf {wrf_dir}/WPS/ungrib {sim_dir}/WPS/')
        os.system(f'ln -sf {wrf_dir}/WPS/metgrid {sim_dir}/WPS/')
        shutil.copy(src=f'{wrf_dir}/WPS/namelist.wps', dst=f'{sim_dir}/WPS/namelist.wps')

        os.system(f'sed -i s/start_date.*$/"start_date = \'{start_time}\', \'{start_time}\', \'{start_time}\',"/g {sim_dir}/WPS/namelist.wps')
        os.system(f'sed -i s/end_date.*$/"end_date = \'{end_time}\', \'{end_time}\', \'{end_time}\',"/g {sim_dir}/WPS/namelist.wps')
        os.system(f'sed -i s/ref_lat.*$/"ref_lat = {lat}"/g {sim_dir}/WPS/namelist.wps')
        os.system(f'sed -i s/ref_lon.*$/"ref_lon = {lon}"/g {sim_dir}/WPS/namelist.wps')
        os.system(f'sed -i s/truelat1.*$/"truelat1 = {lat}"/g {sim_dir}/WPS/namelist.wps')
        os.system(f'sed -i s/stand_lon.*$/"stand_lon = {lon}"/g {sim_dir}/WPS/namelist.wps')
    else:
        print('Skipping existing WPS...')

    # WRF setup. Link executables + data files, copy and update namelist.
    if not os.path.exists(f'{sim_dir}/WRF/'):
        os.mkdir(f'{sim_dir}/WRF')
    
    for mp in mp_schemes.keys():
        if not os.path.exists(f'{sim_dir}/WRF/{mp}'):
            os.mkdir(f'{sim_dir}/WRF/{mp}')
            
            os.system(f'ln -sf {wrf_dir}/WRF/run/* {sim_dir}/WRF/{mp}/')
            os.system(f'rm {sim_dir}/WRF/{mp}/namelist.* {sim_dir}/WRF/{mp}/*.sh')
            shutil.copy(src=f'{wrf_dir}/WRF/run/namelist.input', dst=f'{sim_dir}/WRF/{mp}/namelist.input')

            os.system(f'sed -i s/start_year.*$/"start_year = {start_time[0:4]}, {start_time[0:4]}, {start_time[0:4]},/g" {sim_dir}/WRF/{mp}/namelist.input')
            os.system(f'sed -i s/start_month.*$/"start_month = {start_time[5:7]}, {start_time[5:7]}, {start_time[5:7]},/g" {sim_dir}/WRF/{mp}/namelist.input')
            os.system(f'sed -i s/start_day.*$/"start_day = {start_time[8:10]}, {start_time[8:10]}, {start_time[8:10]},/g" {sim_dir}/WRF/{mp}/namelist.input')
            os.system(f'sed -i s/start_hour.*$/"start_hour = {start_time[11:13]}, {start_time[11:13]}, {start_time[11:13]},/g" {sim_dir}/WRF/{mp}/namelist.input')
            os.system(f'sed -i s/end_year.*$/"end_year = {end_time[0:4]}, {end_time[0:4]}, {end_time[0:4]},/g" {sim_dir}/WRF/{mp}/namelist.input')
            os.system(f'sed -i s/end_month.*$/"end_month = {end_time[5:7]}, {end_time[5:7]}, {end_time[5:7]},/g" {sim_dir}/WRF/{mp}/namelist.input')
            os.system(f'sed -i s/end_day.*$/"end_day = {end_time[8:10]}, {end_time[8:10]}, {end_time[8:10]},/g" {sim_dir}/WRF/{mp}/namelist.input')
            os.system(f'sed -i s/end_hour.*$/"end_hour = {end_time[11:13]}, {end_time[11:13]}, {end_time[11:13]},/g" {sim_dir}/WRF/{mp}/namelist.input')
            os.system(f'sed -i s/mp_physics.*$/"mp_physics = {mp_schemes[mp]}, {mp_schemes[mp]}, {mp_schemes[mp]},/g" {sim_dir}/WRF/{mp}/namelist.input')
        else:
            print(f'Skipping existing WRF/{mp}...')