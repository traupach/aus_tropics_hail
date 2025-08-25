"""Functions to help with investigating simulations of hail in northern Australia."""

import math
import os
import shutil

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import metpy.calc as mpcalc
import numpy as np
import pandas as pd
import seaborn as sns
import xarray
from cartopy.mpl.geoaxes import GeoAxes
from matplotlib import gridspec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon
from matplotlib.ticker import MaxNLocator, ScalarFormatter
from metpy.plots import SkewT
from metpy.units import units
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


def sim_directory(lat, lon, year, month, day, hour, minute, sims_dir):  # noqa: D103
    return f'{sims_dir}/lat_{lat:.3f}_lon_{lon:.3f}_{year:.0f}-{month:02.0f}-{day:02.0f}_{hour:02.0f}:{minute:02.0f}'


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
        mp_schemes = {'P3-3M': 53, 'MY2': 9, 'NSSL': 18, 'Thompson': 8}

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
                f'sed -i s/start_year.*$/"start_year = {start_time[0:4]}, {start_time[0:4]}, {start_time[0:4]},/g" {sim_dir}/WRF/{mp}/namelist.input',
            )
            os.system(
                f'sed -i s/start_month.*$/"start_month = {start_time[5:7]}, {start_time[5:7]}'
                f', {start_time[5:7]},/g" {sim_dir}/WRF/{mp}/namelist.input',
            )
            os.system(
                f'sed -i s/start_day.*$/"start_day = {start_time[8:10]}, {start_time[8:10]}'
                f', {start_time[8:10]},/g" {sim_dir}/WRF/{mp}/namelist.input',
            )
            os.system(
                f'sed -i s/start_hour.*$/"start_hour = {start_time[11:13]}, {start_time[11:13]}'
                f', {start_time[11:13]},/g" {sim_dir}/WRF/{mp}/namelist.input',
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


def open_data(hail_detections, sims_dir, mps=None, basic=True, conv=True, interp=True):
    """Open the data for the tropical hail experiments.

    Arguments:
        hail_detections: Hail detection times to open for.
        sims_dir: The base directory for the model outputs.
        mps: The names of the microphysics schemes to read in.
        domain: The name of the WRF domain to read and match with other data.
        basic: include basic data?
        conv: include convective data?
        interp: include interpolated levels?

    Returns: A combined dataset of data.

    """
    if mps is None:
        mps = ['NSSL', 'MY2', 'P3-3M', 'Thompson']

    all_dat = []

    for i, row in hail_detections.iterrows():
        base_dr = sim_directory(
            lat=row.latitude,
            lon=row.longitude,
            year=row.year,
            month=row.month,
            day=row.day,
            hour=row.hour,
            minute=row.minute,
            sims_dir=sims_dir,
        )

        for mp in mps:
            dr = f'{base_dr}/WRF/{mp}/'

            event_basic = xarray.Dataset()
            event_conv = xarray.Dataset()
            event_pressure_level = xarray.Dataset()

            # Open basic data.
            if basic:
                event_basic = xarray.open_mfdataset(f'{dr}/basic*.nc', parallel=True, chunks={'time': 30})
                event_basic = event_basic[['hailcast_diam_max', 'latitude', 'longitude', 'mdbz',
                                           'ctt', 'pw', 'graupel_max', 'updraft_helicity', 'hail_maxk1']]

            # Open conv data.
            if conv:
                event_conv = xarray.open_mfdataset(f'{dr}/conv*.nc', parallel=True)

            # Open pressure-level interpolated fields.
            if interp:
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


def plot_hail_simulations(dat, figsize=(9.6, 3), marker_size=80, r=0.2, xlim=None, ylim=None, file=None):
    """Plot where hail was and was not simulated, by MP scheme and event.

    Arguments:
        dat: Containing event_includes_hail, event_latitude, event_longitude, mp_scheme, and event.
        figsize: Figure width x height.
        marker_size: Marker size for plot.
        r: Radius around the event location to spread the individual points in a circle.
        xlim: Limits for x axis.
        ylim: Limits for y axis.
        file: Filename to write plot to.

    """
    sims = dat[['event_includes_hail', 'event_latitude', 'event_longitude']].to_dataframe().reset_index()

    for i, mp in enumerate(dat.mp_scheme.values):
        angle = 2 * math.pi * i / len(dat.mp_scheme)  # angle in radians
        sims.loc[sims.mp_scheme == mp, 'event_longitude'] += r * math.cos(angle)
        sims.loc[sims.mp_scheme == mp, 'event_latitude'] += +r * math.sin(angle)

    sims = sims.rename(columns={'event_includes_hail': 'Hail', 'mp_scheme': 'MP scheme'})

    _, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()}, figsize=figsize)
    sns.scatterplot(
        data=sims,
        x='event_longitude',
        y='event_latitude',
        s=marker_size,
        markers=['X', 'o'],
        hue='MP scheme',
        style='Hail',
        ax=ax,
        transform=ccrs.PlateCarree(),
    )
    ax.coastlines()

    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, alpha=0.5)
    gl.top_labels = gl.right_labels = False

    ax.set_xlabel('Longitude [$^{\circ}$ E]')
    ax.set_ylabel('Latitude [$^{\circ}$ S]')

    sns.move_legend(ax, 'upper left', bbox_to_anchor=(1, 1.02))

    # Add inset globe to show map location.
    inset_ax = inset_axes(
        ax,
        width=1.5,
        height=1.5,
        loc='center left',
        bbox_to_anchor=(0.975, 0.215),
        bbox_transform=ax.transAxes,
        borderpad=2,
        axes_class=GeoAxes,
        axes_kwargs={'projection': ccrs.NearsidePerspective(central_longitude=135, central_latitude=-25, satellite_height=35785831 / 5)},
    )
    inset_ax.add_feature(cfeature.LAND, zorder=0)
    inset_ax.add_feature(cfeature.OCEAN, zorder=0)
    inset_ax.add_feature(cfeature.COASTLINE)

    # Patch to highlight plotted region.
    extent_box = [(xlim[0], ylim[0]), (xlim[1], ylim[0]), (xlim[1], ylim[1]), (xlim[0], ylim[1]), (xlim[0], ylim[0])]
    patch = Polygon(extent_box, closed=True, transform=ccrs.PlateCarree(), facecolor='red', edgecolor='black', linewidth=0.2, alpha=0.7)
    inset_ax.add_patch(patch)

    inset_ax.set_global()

    if file is not None:
        plt.savefig(file, dpi=300, bbox_inches='tight')

    plt.show()


def comp_profiles(
    dat,
    variables,
    varnames,
    time_slice=slice(None, None),
    figsize=(12, 12),
    hail_colour='#EC18DE',
    nohail_colour='#05A703',
    file=None,
    factor=1,
    wspace=0.1,
    hspace=0.32,
    mps=['MY2', 'NSSL', 'Thompson', 'P3-3M']
):
    """Compare vertical profiles of seleted variables by hail/no hail.

    Args:
        dat: The data to use to compare, often spatial means.
        variables: Variables to include (as one per column).
        varnames: Dictionary of variable: label.
        time_slice: Slices of time (isel) to use; default to all.
        figsize: Figure size.
        hail_colour: Colour for hail profiles.
        nohail_colour: Colour for no-hail profiles.
        file: Output file.
        factor: Multiply mean and std by this factor before plotting.
        wspace: Width spacing for subplots.
        hspace: Height spacing for subplots.
        mps: MP schemes to plot, in row order.

    """
    v = [*variables, 'event_includes_hail']

    means = dat[v].isel(timestep=time_slice).to_dataframe().reset_index().groupby(['mp_scheme', 'pressure_level', 'event_includes_hail']).mean()
    sds = dat[v].isel(timestep=time_slice).to_dataframe().reset_index().groupby(['mp_scheme', 'pressure_level', 'event_includes_hail']).std()

    means = means.drop(columns=['timestep', 'event'])
    sds = sds.drop(columns=['timestep', 'event'])

    means = means.reset_index().melt(id_vars=['mp_scheme', 'pressure_level', 'event_includes_hail'], value_name='mean')
    sds = sds.reset_index().melt(id_vars=['mp_scheme', 'pressure_level', 'event_includes_hail'], value_name='std')

    means = means.set_index(['mp_scheme', 'pressure_level', 'event_includes_hail', 'variable'])
    sds = sds.set_index(['mp_scheme', 'pressure_level', 'event_includes_hail', 'variable'])
    stats = means.join(sds).reset_index()
    stats = stats.sort_values(['mp_scheme', 'event_includes_hail', 'pressure_level'])

    stats['min'] = stats['mean'] - stats['std']
    stats['max'] = stats['mean'] + stats['std']
    stats['mean'] = stats['mean'] * factor
    stats['std'] = stats['std'] * factor

    hail_cols = {False: nohail_colour, True: hail_colour}

    fig, axs = plt.subplots(ncols=len(variables), nrows=len(mps), figsize=figsize, gridspec_kw={'wspace': wspace, 'hspace': hspace})

    for m, mp in enumerate(mps):
        for i, v in enumerate(variables):
            s = stats[np.logical_and(stats['variable'] == v, stats['mp_scheme'] == mp)]

            if np.all(np.isnan(s['mean'])):
                axs[m, i].set_visible(False)
                if m > 0:
                    axs[m-1, i].set_xlabel(varnames[v])
                continue

            sns.lineplot(
                s,
                x='mean',
                y='pressure_level',
                hue='event_includes_hail',
                ax=axs[m, i],
                sort=False,
                estimator=None,
                legend=False,
                palette=hail_cols,
            )

            for ih in [False, True]:
                rib = s[s.event_includes_hail == ih]
                axs[m, i].fill_betweenx(rib['pressure_level'], rib['mean'] - rib['std'], rib['mean'] + rib['std'], color=hail_cols[ih], alpha=0.2)

            axs[m, i].invert_yaxis()
            axs[m, i].set_ylabel('Pressure [hPa]')
            axs[m, i].set_xlabel(varnames[v])

            if m < len(mps) - 1:
                axs[m, i].set_xlabel('')

            if i > 0:
                axs[m, i].set_yticklabels([])
                axs[m, i].set_ylabel('')

            formatter = ScalarFormatter(useMathText=True)
            formatter.set_scientific(True)
            formatter.set_powerlimits((-3, 4))
            axs[m, i].xaxis.set_major_formatter(formatter)
            axs[m, i].xaxis.set_major_locator(MaxNLocator(nbins=2))

            axs[m, i].set_title(mp)

    legend_elements = [
        Line2D([0], [0], color=hail_colour, label='Hail-event profile'),
        Patch(facecolor=hail_colour, label='Hail-event std. dev. range', alpha=0.5),
        Line2D([0], [0], color=nohail_colour, label='No-hail-event profile'),
        Patch(facecolor=nohail_colour, label='No-hail-event std. dev. range', alpha=0.5),
    ]

    fig.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.05))

    if file is not None:
        plt.savefig(file, dpi=300, bbox_inches='tight')

    plt.show()


def skew_T_comp(
    dat,
    time_slice=slice(None, None),
    figsize=(12, 3),
    yticks=None,
    xticks=None,
    hail_colour='#EC18DE',
    nohail_colour='#05A703',
    xlim=(-40, 38),
    ylim=(1000, 150),
    alpha=0.2,
    wspace=0.1,
    hspace=0.1,
    file=None,
):
    """Compare Skew_Ts per mp scheme.

    Args:
        dat: Data to compare (spatial means).
        time_slice: isel slice to use for timesteps (defaults to all).
        figsize: Defaults to (12, 3).
        yticks: Defaults to [1000, 700, 500, 300, 200].
        xticks: Defaults to [-30, -15, 0, 15, 30].
        hail_colour: Defaults to '#EC18DE'.
        nohail_colour: Defaults to '#05A703'.
        xlim: Defaults to (-40, 38).
        ylim:Defaults to (1000, 150).
        alpha: Line alpha value.
        wspace: Width spacing for subplots.
        hspace: Height spacing for subplots.
        file: Output file to write.

    """
    if yticks is None:
        yticks = [1000, 700, 500, 300, 200]
    if xticks is None:
        xticks = [-30, -15, 0, 15, 30]

    mps = np.unique(dat.mp_scheme.values)
    hail_profs = dat.isel(timestep=time_slice).where(dat.event_includes_hail == True)  # noqa: E712
    nohail_profs = dat.isel(timestep=time_slice).where(dat.event_includes_hail == False)  # noqa: E712

    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(1, len(mps) + 1, wspace=wspace, hspace=hspace)

    for i, mp in enumerate(mps):
        skew = SkewT(fig, subplot=gs[i])

        p = hail_profs.pressure_level.values * units.hPa
        T_hail_mean = hail_profs.sel(mp_scheme=mp).temperature_at_p.mean(['timestep', 'event']).values  # noqa: N806
        T_hail_sd = hail_profs.sel(mp_scheme=mp).temperature_at_p.std(['timestep', 'event']).values  # noqa: N806

        T_nohail_mean = nohail_profs.sel(mp_scheme=mp).temperature_at_p.mean(['timestep', 'event']).values  # noqa: N806
        T_nohail_sd = nohail_profs.sel(mp_scheme=mp).temperature_at_p.std(['timestep', 'event']).values  # noqa: N806

        dp_hail_mean = hail_profs.sel(mp_scheme=mp).td_at_p.mean(['timestep', 'event']).values
        dp_nohail_mean = nohail_profs.sel(mp_scheme=mp).td_at_p.mean(['timestep', 'event']).values

        dp_hail_sd = hail_profs.sel(mp_scheme=mp).td_at_p.std(['timestep', 'event']).values
        dp_nohail_sd = nohail_profs.sel(mp_scheme=mp).td_at_p.std(['timestep', 'event']).values

        skew.plot(p, T_hail_mean * units.K, hail_colour)
        skew.plot(p, dp_hail_mean * units.degreeC, hail_colour, linestyle='--')
        skew.ax.fill_betweenx(
            p,
            (dp_hail_mean - dp_hail_sd) * units.degreeC,
            (dp_hail_mean + dp_hail_sd) * units.degreeC,
            color=hail_colour,
            alpha=alpha,
        )
        skew.ax.fill_betweenx(
            p,
            (T_hail_mean - T_hail_sd) * units.K,
            (T_hail_mean + T_hail_sd) * units.K,
            color=hail_colour,
            alpha=alpha,
        )

        skew.plot(p, T_nohail_mean * units.K, nohail_colour)
        skew.plot(p, dp_nohail_mean * units.degreeC, nohail_colour, linestyle='--')
        skew.ax.fill_betweenx(
            p,
            (dp_nohail_mean - dp_nohail_sd) * units.degreeC,
            (dp_nohail_mean + dp_nohail_sd) * units.degreeC,
            color=nohail_colour,
            alpha=alpha,
        )
        skew.ax.fill_betweenx(
            p,
            (T_nohail_mean - T_nohail_sd) * units.K,
            (T_nohail_mean + T_nohail_sd) * units.K,
            color=nohail_colour,
            alpha=alpha,
        )

        # Calculate lifted parcel profile for surface parcel, based on mean temp/humidity at surface.
        surf_T = ((T_hail_mean[-1] + T_nohail_mean[-1]) / 2) * units.K  # noqa: N806
        surf_dp = ((dp_hail_mean[-1] + dp_nohail_mean[-1]) / 2) * units.degreeC
        prof = mpcalc.parcel_profile(pressure=p[::-1], temperature=surf_T, dewpoint=surf_dp)[::-1]
        skew.plot(p, prof, 'black', linewidth=1)

        skew.ax.set_title(mp)
        skew.ax.set_yticks(yticks)
        skew.ax.set_ylabel('Pressure [hPa]')
        skew.ax.set_xticks(xticks)
        skew.ax.set_xlabel('T [$^{\circ}$C]')
        skew.ax.set_xlim(xlim)
        skew.ax.set_ylim(ylim)

        if i > 0:
            skew.ax.set_yticklabels([])
            skew.ax.set_ylabel('')

    legend_elements = [
        Line2D([0], [0], color=hail_colour, label='H temp.'),
        Line2D([0], [0], color=hail_colour, linestyle='--', label='H dewpoint'),
        Patch(facecolor=hail_colour, label='H std. dev.', alpha=alpha),
        Line2D([0], [0], color=nohail_colour, label='NH temp.'),
        Line2D([0], [0], color=nohail_colour, linestyle='--', label='NH dewpoint'),
        Patch(facecolor=nohail_colour, label='NH std. dev.', alpha=alpha),
    ]

    legend_ax = fig.add_subplot(gs[len(mps) : len(mps) + 1])
    legend_ax.axis('off')
    legend_ax.legend(handles=legend_elements, loc='center')

    if file is not None:
        plt.savefig(file, dpi=300, bbox_inches='tight')

    plt.show()

def read_data(hail_detections, sims_dir, results_files=None, analysis_timesteps=slice(-24, -12), hail_threshold=20):
    """Read data from all simulations and make spatial stats. Cache as required.

    Args:
        hail_detections: Hail detections to read for.
        sims_dir: Directory where simulations are stored.
        results_files: Files to read for results.
        analysis_timesteps: Timesteps to analyse (default: hour of the event).
        hail_threshold: Require hail to be over this many mm to count as hail.

    """
    if results_files is None:
        results_files = ['results/spatial_means.nc', 'results/spatial_maxes.nc', 'results/spatial_mins.nc']

    if not np.all([os.path.exists(x) for x in results_files]):
        dat = open_data(hail_detections=hail_detections, sims_dir=sims_dir)
        dat = dat.chunk({'event': 5, 'mp_scheme': 1, 'south_north': -1, 'west_east': -1, 'pressure_level': -1, 'timestep': 12})
        dat = dat.isel(timestep=analysis_timesteps)

        dat['event_includes_hail'] = (dat.hailcast_diam_max.max(['timestep', 'south_north', 'west_east']) >= hail_threshold).load()
        dat['event_latitude'] = dat.latitude.mean(['timestep', 'south_north', 'west_east']).load()
        dat['event_longitude'] = dat.longitude.mean(['timestep', 'south_north', 'west_east']).load()

        files = {}
        if not os.path.exists('results/spatial_means.nc'):
            print('Spatial means...')
            spatial_means = dat.mean(['south_north', 'west_east'], keep_attrs=True).load()
            files['results/spatial_means.nc'] = spatial_means
        if not os.path.exists('results/spatial_maxes.nc'):
            print('Spatial maxes...')
            spatial_maxes = dat.max(['south_north', 'west_east'], keep_attrs=True).load()
            files['results/spatial_maxes.nc'] = spatial_maxes
        if not os.path.exists('results/spatial_mins.nc'):
            print('Spatial maxes...')
            spatial_mins = dat.min(['south_north', 'west_east'], keep_attrs=True).load()
            files['results/spatial_mins.nc'] = spatial_mins

        comp = {'zlib': True, 'complevel': 5}
        for file in files:
            ds = files[file]
            encoding = {var: comp for var in ds.data_vars}
            ds.to_netcdf(file, encoding=encoding)

    spatial_means = xarray.open_dataset('results/spatial_means.nc')
    spatial_maxes = xarray.open_dataset('results/spatial_maxes.nc')
    spatial_mins = xarray.open_dataset('results/spatial_mins.nc')

    return spatial_means, spatial_maxes, spatial_mins

def plot_extrema(mins, maxes, file=None, figsize=(12,12), hail_colour='#EC18DE', nohail_colour='#05A703'):
    """Plot distributions of mins and maxes.

    Args:
        mins: Mins to plot.
        maxes: Maxes to plot.
        file: Output file for plot.
        figsize: Figure size.
        hail_colour: Colour for hail distributions.
        nohail_colour: Colour for no-hail distributions.

    """
    mins_stacked = mins.stack({'sample': ['timestep', 'event']})
    maxes_stacked = maxes.stack({'sample': ['timestep', 'event']})

    assert mins_stacked.event_includes_hail.equals(maxes_stacked.event_includes_hail), 'Mismatch in hail flags'
    plot_cols = {
        'min_ctt': 'Minimum cloud top temperature',
        'min_updraft_helicity': 'Minimum updraft helicity',
        'max_mdbz': 'Maximum radar reflectivity',
        'max_hailcast_diam': 'Maximum HAILCAST diameter',
        'max_graupel_max': 'Maximum column-integrated graupel',
        'max_shear_magnitude': 'Maximum 0-6 km bulk wind shear',
        'min_freezing_level': 'Maximum freezing level height',
        'min_temp_500': 'Minimum temperature at 500 hPa',
        'max_cape': 'Maximum CAPE',
        'min_cin': 'Minimum CIN',
        'min_lapse_rate': 'Minimum 700 hPa to 500 hPa lapse rate',
        'max_pw': 'Maximum precipitable water',
    }

    stats = (
        xarray.Dataset(
            {
                'min_ctt': mins_stacked.ctt,
                'min_updraft_helicity': mins_stacked.updraft_helicity,
                'max_mdbz': maxes_stacked.mdbz,
                'max_hailcast_diam': maxes_stacked.hailcast_diam_max,
                'max_graupel_max': maxes_stacked.graupel_max,
                'max_shear_magnitude': maxes_stacked.shear_magnitude,
                'min_freezing_level': mins_stacked.freezing_level,
                'min_temp_500': mins_stacked.temp_500,
                'max_cape': maxes_stacked.mixed_100_cape,
                'min_cin': mins_stacked.mixed_100_cin,
                'min_lapse_rate': mins_stacked.lapse_rate_700_500,
                'event_includes_hail': mins_stacked.event_includes_hail,
                'max_pw': maxes_stacked.pw,
            },
        )
    )

    stats_table = stats.unstack().to_dataframe().reset_index()
    unit_renamer = {'degC': '$^{\circ}$C',
                    'kg m-2': 'km m$^{-2}$',
                    'm2 s-2': 'm$^2$ s$^{-2}$'}


    hail_cols = {False: nohail_colour, True: hail_colour}
    _, axs = plt.subplots(ncols=2, nrows=6, figsize=figsize, gridspec_kw={'hspace': 0.3, 'wspace': 0.05})

    for i, v in enumerate(plot_cols):
        sns.boxplot(stats_table, y=v, x='mp_scheme', ax=axs.flat[i], hue='event_includes_hail',
                    width=0.5, legend=i==len(plot_cols)-1, palette=hail_cols)
        axs.flat[i].set_xlabel('')

        col = (i % 2) + 1
        row = (i // 2) + 1

        if row != len(plot_cols)/2:
            axs.flat[i].set_xticks([])
        axs.flat[i].set_title(plot_cols[v])

        u = stats[v].attrs['units']
        axs.flat[i].set_ylabel(unit_renamer.get(u, u))

        if col == 2:  # noqa: PLR2004
            axs.flat[i].yaxis.tick_right()
            axs.flat[i].yaxis.set_label_position("right")

    sns.move_legend(axs.flat[i], 'center', bbox_to_anchor=(0, -0.75), title='Surface hail')

    if file is not None:
        plt.savefig(file, dpi=300, bbox_inches='tight')

    plt.show()

def plot_surface_hailsizes(spatial_maxes, figsize=(6,4), file=None, damaging_threshold=20, renamer=None, width=0.4):
    """Plot a comparison of surface hail sizes using HAILCAST vs microphysics schemes.

    Args:
        spatial_maxes: Spatial maxima including hail_maxk1 and hailcast_diam_max.
        figsize: Figure size. Defaults to (6,4).
        file: Plot to this (optional) file.
        damaging_threshold: Damaging hail threshold in mm.
        rename: Rename variables?
        width: Width for bars.

    """
    if renamer is None:
        renamer = {'hail_maxk1': 'MP scheme', 'hailcast_diam_max': 'HAILCAST'}

    surface_hailsizes = spatial_maxes[['hail_maxk1', 'hailcast_diam_max']].to_dataframe().reset_index()
    surface_hailsizes['hail_maxk1'] = surface_hailsizes['hail_maxk1'] * 1000 # Adjust from m to mm
    surface_hailsizes['hail_maxk1'] = surface_hailsizes['hail_maxk1'].where(surface_hailsizes['hail_maxk1'] > 0)
    surface_hailsizes['hailcast_diam_max'] = surface_hailsizes['hailcast_diam_max'].where(surface_hailsizes['hailcast_diam_max'] > 0)

    # True/False when hailcast or MP scheme shows damaging hail.
    damaging_occurrences = surface_hailsizes[['mp_scheme', 'event', 'hailcast_diam_max', 'hail_maxk1']].copy()
    damaging_occurrences['hailcast_diam_max'] = damaging_occurrences['hailcast_diam_max'] >= damaging_threshold
    damaging_occurrences['hail_maxk1'] = damaging_occurrences['hail_maxk1'] >= damaging_threshold
    damaging_events = (damaging_occurrences.groupby(['mp_scheme', 'event']).sum() > 0).groupby('mp_scheme').sum().reset_index()

    surface_hailsizes = surface_hailsizes.dropna(how='all', subset=['hail_maxk1', 'hailcast_diam_max'])
    surface_hailsizes = surface_hailsizes.rename(columns=renamer)
    surface_hailsizes = surface_hailsizes.melt(id_vars=['timestep', 'event', 'mp_scheme'])

    _, ax = plt.subplots(figsize=figsize)
    colors = ['#E69F00', '#56B4E9', '#009E73', '#F0E442']
    sns.boxplot(surface_hailsizes, x='variable', y='value', hue='mp_scheme', ax=ax, palette=colors, width=width)
    ax.set_ylabel('Hail diameter [mm]')
    ax.set_xlabel('')
    ax.legend(title='Microphysics scheme')

    numbars = len(spatial_maxes.mp_scheme.values)

    for j, x in enumerate(renamer):
        from_x = j - 0.5 * width

        for i, mp in enumerate(spatial_maxes.mp_scheme.values):
            offset = i*width/numbars + (width/numbars/2)
            txt = damaging_events.loc[damaging_events['mp_scheme'] == mp, x].values[0]
            if txt != 0:
                ax.text(x=from_x + offset, y=-10, ha='center', s=txt)

    ax.set_ylim(-20, np.max(surface_hailsizes['value']) * 1.1)

    if file is not None:
            plt.savefig(file, dpi=300, bbox_inches='tight')

    plt.tight_layout()
    plt.show()

    hailcast_cases = int((spatial_maxes.sel(mp_scheme=['MY2', 'NSSL', 'Thompson']).hailcast_diam_max.max('timestep') > 20).sum().values)
    mp_cases = int((spatial_maxes.sel(mp_scheme=['MY2', 'NSSL', 'Thompson']).hail_maxk1.max('timestep') * 1000 > 20).sum().values)

    return hailcast_cases, mp_cases