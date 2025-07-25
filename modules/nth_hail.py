import os  # noqa: D100
import shutil

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import xarray


def sim_directory(lat, lon, year, month, day, hour, minute, sims_dir):  # noqa: D103
    return f'{sims_dir}/lat_{lat}_lon_{lon}_{year}-{month}-{day}_{hour:02}:{minute:02}'


def set_up_WRF(lat, lon, year, month, day, hour, minute, start_time, end_time, namelist_dir, wrf_dir, sims_dir, mp_schemes=None):
    """Set up directories ready for WPS and WRF runs for a given event, including updating namelist files.

    Arguments:
        lat: Event latitude.
        lon: Event longitude.
        year: Event year.
        month: Event month.
        day: Event day.
        hour: Event hour.
        minute: Event minute.
        start_time: Simulation start time as %Y-%m-%d_%H:%M:%S.
        end_time: Simulation end time as %Y-%m-%d_%H:%M:%S.
        wrf_dir: Directory with compiled WRF and basic namelist files.
        namelist_dir: Namelist directory to copy template namelists from.
        sims_dir: Output directory where simulations will be run.
        mp_schemes: Microphysics options to use; each will have a subdirectory under WRF.

    """
    if mp_schemes is None:
        mp_schemes = {'P3-3M': 53, 'MY2': 9, 'NSSL': 17, 'Thompson': 8}

    sim_dir = f'{sims_dir}/lat_{lat:.3f}_lon_{lon:.3f}_{year:.0f}-{month:02.0f}-{day:02.0f}_{hour:02.0f}:{minute:02.0f}'
    if not os.path.exists(sim_dir):
        os.mkdir(sim_dir)

    # WPS setup. Link executables + data files, copy and update namelist.
    if not os.path.exists(f'{sim_dir}/WPS'):
        os.mkdir(f'{sim_dir}/WPS')
        os.system(f'ln -sf {wrf_dir}/WPS/* {sim_dir}/WPS/')
        os.system(f'rm -f {sim_dir}/WPS/namelist.wps')
        shutil.copy(src=f'{namelist_dir}/WPS/namelist.wps', dst=f'{sim_dir}/WPS/namelist.wps')

        os.system(f"sed -i s/start_date.*$/\"start_date = '{start_time}', '{start_time}', '{start_time}',\"/g {sim_dir}/WPS/namelist.wps")
        os.system(f"sed -i s/end_date.*$/\"end_date = '{end_time}', '{end_time}', '{end_time}',\"/g {sim_dir}/WPS/namelist.wps")
        os.system(f'sed -i s/ref_lat.*$/"ref_lat = {lat}"/g {sim_dir}/WPS/namelist.wps')
        os.system(f'sed -i s/ref_lon.*$/"ref_lon = {lon}"/g {sim_dir}/WPS/namelist.wps')
        os.system(f'sed -i s/truelat1.*$/"truelat1 = {lat}"/g {sim_dir}/WPS/namelist.wps')
        os.system(f'sed -i s/stand_lon.*$/"stand_lon = {lon}"/g {sim_dir}/WPS/namelist.wps')
    else:
        print('Skipping existing WPS...')

    # WRF setup. Link executables + data files, copy and update namelist.
    if not os.path.exists(f'{sim_dir}/WRF/'):
        os.mkdir(f'{sim_dir}/WRF')

    for mp in mp_schemes:
        if not os.path.exists(f'{sim_dir}/WRF/{mp}'):
            os.mkdir(f'{sim_dir}/WRF/{mp}')

            os.system(f'ln -sf {wrf_dir}/WRF/* {sim_dir}/WRF/{mp}/')
            os.system(f'rm -f {sim_dir}/WRF/{mp}/namelist.input')
            shutil.copy(src=f'{namelist_dir}/WRF/namelist.input', dst=f'{sim_dir}/WRF/{mp}/namelist.input')

            os.system(
                f'sed -i s/start_year.*$/"start_year = {start_time[0:4]}, {start_time[0:4]}'
                f', {start_time[0:4]},/g" {sim_dir}/WRF/{mp}/namelist.input'
            )
            os.system(
                f'sed -i s/start_month.*$/"start_month = {start_time[5:7]}, {start_time[5:7]}'
                f', {start_time[5:7]},/g" {sim_dir}/WRF/{mp}/namelist.input'
            )
            os.system(
                f'sed -i s/start_day.*$/"start_day = {start_time[8:10]}, {start_time[8:10]}'
                f', {start_time[8:10]},/g" {sim_dir}/WRF/{mp}/namelist.input'
            )
            os.system(
                f'sed -i s/start_hour.*$/"start_hour = {start_time[11:13]}, {start_time[11:13]}'
                f', {start_time[11:13]},/g" {sim_dir}/WRF/{mp}/namelist.input'
            )
            os.system(f'sed -i s/end_year.*$/"end_year = {end_time[0:4]}, {end_time[0:4]}, {end_time[0:4]},/g" {sim_dir}/WRF/{mp}/namelist.input')
            os.system(f'sed -i s/end_month.*$/"end_month = {end_time[5:7]}, {end_time[5:7]}, {end_time[5:7]},/g" {sim_dir}/WRF/{mp}/namelist.input')
            os.system(f'sed -i s/end_day.*$/"end_day = {end_time[8:10]}, {end_time[8:10]}, {end_time[8:10]},/g" {sim_dir}/WRF/{mp}/namelist.input')
            os.system(
                f'sed -i s/end_hour.*$/"end_hour = {end_time[11:13]}, {end_time[11:13]}, {end_time[11:13]},/g" {sim_dir}/WRF/{mp}/namelist.input',
            )
            os.system(
                f'sed -i s/mp_physics.*$/"mp_physics = {mp_schemes[mp]}, {mp_schemes[mp]}, {mp_schemes[mp]},/g" {sim_dir}/WRF/{mp}/namelist.input',
            )
        else:
            print(f'Skipping existing WRF/{mp}...')


def open_kimberley_data(hail_detections, sims_dir, mps=None):
    """Open the data for the Kimberley hail experiments.

    Arguments:
        hail_detections: Hail detection times to open for.
        sims_dir: The base directory for the model outputs.
        mps: The names of the microphysics schemes to read in.
        domain: The name of the WRF domain to read and match with other data.

    Returns: A combined dataset of data.

    """
    if mps is None:
        mps = ['NSSL', 'MY2', 'P3-3M']

    all_dat = []

    for i, row in hail_detections.iterrows():
        base_dr = sim_directory(
            lat=row.latitude, lon=row.longitude, year=row.year, month=row.month,
            day=row.day, hour=row.hour, minute=row.minute, sims_dir=sims_dir,
        )

        for mp in mps:
            dr = f'{base_dr}/WRF/{mp}/'

            # Open basic data.
            event_basic = xarray.open_mfdataset(f'{dr}/basic*.nc', parallel=True)
            event_basic = event_basic[['hailcast_diam_max', 'latitude', 'longitude']]

            # Open conv data.
            event_conv = xarray.open_mfdataset(f'{dr}/conv*.nc', parallel=True)

            # Open pressure-level interpolated fields.
            event_pressure_level = xarray.open_mfdataset(f'{dr}/pressure_level*.nc', parallel=True)
            event_pressure_level = event_pressure_level.rename({x: f'{x}_at_p' for x in event_pressure_level})

            event_dat = xarray.merge([event_conv, event_pressure_level, event_basic])
            del event_conv, event_pressure_level, event_basic

            # Add event information.
            event_dat['event'] = i + 1
            event_dat = event_dat.assign_coords({'event': event_dat.event})
            event_dat = event_dat.expand_dims('event')

            # Add microphysics information.
            event_dat['mp_scheme'] = mp
            event_dat = event_dat.assign_coords({'mp_scheme': event_dat.mp_scheme})
            event_dat = event_dat.expand_dims('mp_scheme')

            # Make times event-independent.
            event_dat = event_dat.sortby('time')
            event_dat['timestep'] = ('time', np.arange(len(event_dat.time)))
            event_dat = event_dat.swap_dims({'time': 'timestep'}).reset_coords()
            all_dat.append(event_dat)
            del event_dat

    all_dat = [x.stack({'event_scheme': ['event', 'mp_scheme']}) for x in all_dat]
    return xarray.combine_nested(all_dat, concat_dim='event_scheme', combine_attrs='drop_conflicts').unstack('event_scheme')


def plot_hail_simulations(dat, figsize=(9.6, 3)):
    """Plot where hail was and was not simulated, by MP scheme and event.

    Arguments:
        dat: Containing event_includes_hail, event_latitude, event_longitude, mp_scheme, and event.
        figsize: Figure width x height.

    """
    sims = dat[['event_includes_hail', 'event_latitude', 'event_longitude']].to_dataframe()
    sims.loc[sims.mp_scheme == 'MY2', 'event_latitude'] += 0.2
    sims.loc[sims.mp_scheme == 'MY2', 'event_longitude'] += 0.4
    sims.loc[sims.mp_scheme == 'NSSL', 'event_latitude'] += 0.2
    sims.loc[sims.mp_scheme == 'NSSL', 'event_longitude'] -= 0.4
    sims = sims.drop(columns=['event', 'mp_scheme']).reset_index()
    sims = sims.rename(columns={'event_includes_hail': 'Hail', 'mp_scheme': 'MP scheme'})

    _, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()}, figsize=figsize)
    sns.scatterplot(
        data=sims,
        x='event_longitude',
        y='event_latitude',
        s=50,
        markers=['X', 'o'],
        hue='MP scheme',
        style='Hail',
        ax=ax,
        transform=ccrs.PlateCarree(),
    )
    ax.coastlines()
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, alpha=0.5)
    gl.top_labels = gl.right_labels = False
    sns.move_legend(ax, 'upper left', bbox_to_anchor=(1, 1.05))
    plt.show()
