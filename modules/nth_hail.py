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


def open_data(hail_detections, sims_dir, mps=None, basic=True, conv=True, interp=True, domain='d03', subset_to_inner=False):
    """Open the data for the tropical hail experiments.

    Arguments:
        hail_detections: Hail detection times to open for.
        sims_dir: The base directory for the model outputs.
        mps: The names of the microphysics schemes to read in.
        domain: The name of the WRF domain to read and match with other data.
        subset_to_inner: Only return for the inner part of the domain (ie that overlaps with a nested inner domain)?
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
                event_basic = xarray.open_mfdataset(f'{dr}/basic_params_{domain}_*.nc', parallel=True, chunks={'time': 30}, data_vars='all')
                event_basic = event_basic[
                    ['hailcast_diam_max', 'latitude', 'longitude', 'mdbz', 'ctt', 'pw', 'graupel_max', 'updraft_helicity', 'hail_maxk1']
                ]

            # Open conv data.
            if conv:
                event_conv = xarray.open_mfdataset(f'{dr}/conv_params_{domain}_*.nc', parallel=True)

            # Open pressure-level interpolated fields.
            if interp:
                event_pressure_level = xarray.open_mfdataset(f'{dr}/pressure_level_params_{domain}_*.nc', parallel=True)
                event_pressure_level = event_pressure_level.rename({x: f'{x}_at_p' for x in event_pressure_level})

            event_dat = xarray.merge([event_conv, event_pressure_level, event_basic])
            del event_conv, event_pressure_level, event_basic

            # Spatial subset?
            if subset_to_inner:
                assert len(event_dat.south_north) == 120, 'Expected domain of 120x120'  # noqa: PLR2004
                assert len(event_dat.west_east) == 120, 'Expected domain of 120x120'  # noqa: PLR2004
                event_dat = event_dat.isel(south_north=slice(39, 79), west_east=slice(39, 79))

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

    all_dat = [x.stack({'event_scheme': ['event', 'mp_scheme']}) for x in all_dat]  # noqa: PD013
    return xarray.combine_nested(all_dat, concat_dim='event_scheme', combine_attrs='drop_conflicts', data_vars='all').unstack('event_scheme')


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
    assert not np.any(dat.sel(mp_scheme='P3-3M')['event_includes_hail_micro']), 'P3 is assumed not to contain hail_maxk1'
    sims = dat[['event_includes_hail_hailcast', 'event_includes_hail_micro', 'event_latitude', 'event_longitude']].to_dataframe().reset_index()

    for i, mp in enumerate(dat.mp_scheme.values):
        angle = 2 * math.pi * i / len(dat.mp_scheme)  # Angle in radians.
        sims.loc[sims.mp_scheme == mp, 'event_longitude'] += r * math.cos(angle)
        sims.loc[sims.mp_scheme == mp, 'event_latitude'] += +r * math.sin(angle)

    _, axs = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()}, figsize=figsize, nrows=2)

    titles = {'event_includes_hail_hailcast': 'HAILCAST', 'event_includes_hail_micro': 'Model microphysics'}
    for i, ind in enumerate(['event_includes_hail_hailcast', 'event_includes_hail_micro']):
        d = sims.copy()
        if ind == 'event_includes_hail_micro':
            d = d.where(d.mp_scheme != 'P3-3M')  # P3-3M microphysics doesn't calculate surface hail diam.
        d = d.rename(columns={ind: 'Hail', 'mp_scheme': 'MP scheme'})

        sns.scatterplot(
            data=d,
            x='event_longitude',
            y='event_latitude',
            s=marker_size,
            markers=['X', 'o'],
            hue='MP scheme',
            hue_order=['MY2', 'NSSL', 'P3-3M', 'Thompson'],
            style='Hail',
            ax=axs[i],
            transform=ccrs.PlateCarree(),
        )
        axs[i].coastlines()
        axs[i].set_title(titles[ind])

    for ax in axs:
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
    mps=None,
    hail_indicator='HAILCAST',
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
        hail_indicator: Which hail indicator to use - HAILCAST or microphysics?

    """
    if mps is None:
        mps = ['MY2', 'NSSL', 'Thompson', 'P3-3M']

    hail_config = {
            'HAILCAST': (
                'event_includes_hail_hailcast',
                [],
            ),
            'microphysics': (
                'event_includes_hail_micro',
                ['P3-3M'],
            ),
        }

    try:
        hail_flag, drop_mps = hail_config[hail_indicator]
    except KeyError as exc:
        valid = ', '.join(repr(k) for k in hail_config)
        msg = f'hail_indicator must be one of: {valid}'
        raise ValueError(msg) from exc

    v = [*variables, hail_flag]
    mps = [mp for mp in mps if mp not in drop_mps]

    means = dat[v].sel(mp_scheme=mps).isel(timestep=time_slice).to_dataframe().reset_index().groupby(['mp_scheme', 'pressure_level', hail_flag]).mean(numeric_only=True)
    sds = dat[v].sel(mp_scheme=mps).isel(timestep=time_slice).to_dataframe().reset_index().groupby(['mp_scheme', 'pressure_level', hail_flag]).std(numeric_only=True)

    means = means.drop(columns=['timestep', 'event'])
    sds = sds.drop(columns=['timestep', 'event'])

    means = means.reset_index().melt(id_vars=['mp_scheme', 'pressure_level', hail_flag], value_name='mean')
    sds = sds.reset_index().melt(id_vars=['mp_scheme', 'pressure_level', hail_flag], value_name='std')

    means = means.set_index(['mp_scheme', 'pressure_level', hail_flag, 'variable'])
    sds = sds.set_index(['mp_scheme', 'pressure_level', hail_flag, 'variable'])
    stats = means.join(sds).reset_index()
    stats = stats.sort_values(['mp_scheme', hail_flag, 'pressure_level'])

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
                    axs[m - 1, i].set_xlabel(varnames[v])
                continue

            sns.lineplot(
                s,
                x='mean',
                y='pressure_level',
                hue=hail_flag,
                ax=axs[m, i],
                sort=False,
                estimator=None,
                legend=False,
                palette=hail_cols,
            )

            for ih in [False, True]:
                rib = s[s[hail_flag] == ih]
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
    hail_indicator='HAILCAST',
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

    hail_config = {
        'HAILCAST': (
            'event_includes_hail_hailcast',
            [],
        ),
        'microphysics': (
            'event_includes_hail_micro',
            ['P3-3M'],
        ),
    }

    try:
        hail_flag, drop_mps = hail_config[hail_indicator]
    except KeyError as exc:
        valid = ', '.join(repr(k) for k in hail_config)
        msg = f'hail_indicator must be one of: {valid}'
        raise ValueError(msg) from exc

    mps = np.unique(dat.mp_scheme.values)
    hail_profs = dat.isel(timestep=time_slice).where(dat[hail_flag] == True)  # noqa: E712
    nohail_profs = dat.isel(timestep=time_slice).where(dat[hail_flag] == False)  # noqa: E712

    hail_profs = hail_profs.sel(mp_scheme=[mp for mp in hail_profs.mp_scheme.values if mp not in drop_mps])
    nohail_profs = nohail_profs.sel(mp_scheme=[mp for mp in nohail_profs.mp_scheme.values if mp not in drop_mps])

    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(1, len(mps) + 1, wspace=wspace, hspace=hspace)

    for i, mp in enumerate([mp for mp in mps if mp not in drop_mps]):
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


def read_data(
    hail_detections,
    sims_dir,
    domain,
    subset_to_inner=False,
    results_files=None,
    analysis_timesteps=slice(-24, -12),
    hail_threshold=20,
    domain_map=None,
):
    """Read data from all simulations and make spatial stats. Cache as required.

    Args:
        hail_detections: Hail detections to read for.
        sims_dir: Directory where simulations are stored.
        domain: Domain to read for.
        subset_to_inner: Subset to inner domain (to cover nested region)?
        results_files: Files to read for results.
        analysis_timesteps: Timesteps to analyse (default: hour of the event).
        hail_threshold: Require hail to be over this many mm to count as hail.
        domain_map: Domain names per WRF domain.

    """
    if results_files is None:
        results_files = [
            f'results/spatial_means_{domain}.nc',
            f'results/spatial_maxes_{domain}.nc',
            f'results/spatial_mins_{domain}.nc',
            f'results/spatial_counts_{domain}.nc',
        ]
    if domain_map is None:
        domain_map = {'d02': '3 km', 'd03': '1 km'}

    if not np.all([os.path.exists(x) for x in results_files]):
        dat = open_data(hail_detections=hail_detections, sims_dir=sims_dir, domain=domain, subset_to_inner=subset_to_inner)
        dat = dat.chunk({'event': 5, 'mp_scheme': 1, 'south_north': -1, 'west_east': -1, 'pressure_level': -1, 'timestep': 12})
        dat = dat.isel(timestep=analysis_timesteps)

        # Convert hail_maxk1 from m to mm.
        dat['hail_maxk1'] = dat.hail_maxk1 * 1000
        dat.hail_maxk1.attrs['units'] = 'mm'

        # Assign flags for whether hailcast or microphysics scheme saw hail.
        dat['event_includes_hail_hailcast'] = dat.hailcast_diam_max.max(['timestep', 'south_north', 'west_east']) >= hail_threshold
        dat['event_includes_hail_micro'] = dat.hail_maxk1.max(['timestep', 'south_north', 'west_east']) >= hail_threshold

        dat['event_latitude'] = dat.latitude.mean(['timestep', 'south_north', 'west_east']).load()
        dat['event_longitude'] = dat.longitude.mean(['timestep', 'south_north', 'west_east']).load()
        dat.attrs['hail_threshold'] = hail_threshold

        files = {}
        if not os.path.exists(f'results/spatial_means_{domain}.nc'):
            print('Spatial means...')
            spatial_means = dat.mean(['south_north', 'west_east'], keep_attrs=True).load()
            files[f'results/spatial_means_{domain}.nc'] = spatial_means
        if not os.path.exists('results/spatial_maxes_{domain}.nc'):
            print('Spatial maxes...')
            spatial_maxes = dat.max(['south_north', 'west_east'], keep_attrs=True).load()
            files[f'results/spatial_maxes_{domain}.nc'] = spatial_maxes
        if not os.path.exists(f'results/spatial_mins_{domain}.nc'):
            print('Spatial mins...')
            spatial_mins = dat.min(['south_north', 'west_east'], keep_attrs=True).load()
            files[f'results/spatial_mins_{domain}.nc'] = spatial_mins
        if not os.path.exists(f'results/spatial_counts_{domain}.nc'):
            print('Spatial counts...')
            updrafts = dat[['w_at_p']].max('pressure_level').rename({'w_at_p': 'updraft_area'}) > 10  # noqa: PLR2004
            updrafts = updrafts.sum(['south_north', 'west_east'])
            updrafts['event_includes_hail_hailcast'] = dat['event_includes_hail_hailcast']
            updrafts['event_includes_hail_micro'] = dat['event_includes_hail_micro']
            updrafts['updraft_area'].attrs['units'] = 'grid pts'
            updrafts['updraft_area'].attrs['name'] = 'Updraft area'
            updrafts['updraft_area'].attrs['description'] = 'Number of pixels with w > 10 m/s'
            files[f'results/spatial_counts_{domain}.nc'] = updrafts

        comp = {'zlib': True, 'complevel': 5}
        for file in files:
            ds = files[file]
            encoding = {var: comp for var in ds.data_vars}
            ds.to_netcdf(file, encoding=encoding)

    spatial_means = xarray.open_dataset(f'results/spatial_means_{domain}.nc').expand_dims({'domain': [domain_map[domain]]})
    spatial_maxes = xarray.open_dataset(f'results/spatial_maxes_{domain}.nc').expand_dims({'domain': [domain_map[domain]]})
    spatial_mins = xarray.open_dataset(f'results/spatial_mins_{domain}.nc').expand_dims({'domain': [domain_map[domain]]})
    spatial_counts = xarray.open_dataset(f'results/spatial_counts_{domain}.nc').expand_dims({'domain': [domain_map[domain]]})

    return spatial_means, spatial_maxes, spatial_mins, spatial_counts


def plot_extrema(
    mins,
    maxes,
    counts,
    file=None,
    figsize=(12, 12.5),
    colours=None,
    hail_indicator='HAILCAST',
):
    """Plot distributions of mins and maxes.

    Args:
        mins: Mins to plot.
        maxes: Maxes to plot.
        counts: Counts to plot.
        file: Output file for plot.
        figsize: Figure size.
        colours: Colours for event hail flags.
        hail_indicator: either 'HAILCAST' or 'microphysics'.

    """
    if colours is None:
        colours = ['#EC18DE', '#05A703', '#1F77B4', '#FF7F0E']

    hail_config = {
        'HAILCAST': (
            'event_includes_hail_hailcast',
            'hailcast_diam_max',
            [],
        ),
        'microphysics': (
            'event_includes_hail_micro',
            'hail_maxk1',
            ['P3-3M'],
        ),
    }

    try:
        hail_flag, hail_diam, drop_mps = hail_config[hail_indicator]
    except KeyError as exc:
        valid = ', '.join(repr(k) for k in hail_config)
        msg = f'hail_indicator must be one of: {valid}'
        raise ValueError(msg) from exc

    maxes['max_updraft'] = maxes.w_at_p.max(['pressure_level'], keep_attrs=True)
    mins_stacked = mins.stack({'sample': ['timestep', 'event']})  # noqa: PD013
    maxes_stacked = maxes.stack({'sample': ['timestep', 'event']})  # noqa: PD013
    counts_stacked = counts.stack({'sample': ['timestep', 'event']})  # noqa: PD013

    assert mins_stacked[hail_flag].equals(maxes_stacked[hail_flag]), 'Mismatch in hail flags'
    assert mins_stacked[hail_flag].equals(counts_stacked[hail_flag]), 'Mismatch in hail flags'
    plot_cols = {
        'min_ctt': 'Minimum cloud top temperature',
        'min_updraft_helicity': 'Minimum updraft helicity',
        'max_mdbz': 'Maximum radar reflectivity',
        'max_hail_diam': 'Maximum hail diameter',
        'max_graupel_max': 'Maximum column-integrated graupel',
        'max_shear_magnitude': 'Maximum 0-6 km bulk wind shear',
        'min_melting_level': 'Minimum melting level height',
        'min_temp_500': 'Minimum temperature at 500 hPa',
        'max_cape': 'Maximum CAPE',
        'min_cin': 'Minimum CIN',
        'min_lapse_rate': 'Minimum 700 hPa to 500 hPa lapse rate',
        'max_pw': 'Maximum precipitable water',
        'max_updraft': 'Maximum updraft',
        'updraft_area': 'Updraft area',
    }

    stats = xarray.Dataset(
        {
            'min_ctt': mins_stacked.ctt,
            'min_updraft_helicity': mins_stacked.updraft_helicity,
            'max_mdbz': maxes_stacked.mdbz,
            'max_hail_diam': maxes_stacked[hail_diam],
            'max_graupel_max': maxes_stacked.graupel_max,
            'max_shear_magnitude': maxes_stacked.shear_magnitude,
            'min_melting_level': mins_stacked.melting_level,
            'min_temp_500': mins_stacked.temp_500,
            'max_cape': maxes_stacked.mixed_100_cape,
            'min_cin': mins_stacked.mixed_100_cin,
            'min_lapse_rate': mins_stacked.lapse_rate_700_500,
            hail_flag: mins_stacked[hail_flag],
            'max_pw': maxes_stacked.pw,
            'max_updraft': maxes_stacked.max_updraft,
            'updraft_area': counts_stacked.updraft_area,
        },
    )

    stats = stats.sel(mp_scheme=[mp for mp in stats.mp_scheme.values if mp not in drop_mps])

    stats_table = stats.unstack().to_dataframe().reset_index()
    unit_renamer = {'degC': '$^{\circ}$C', 'kg m-2': 'km m$^{-2}$', 'm2 s-2': 'm$^2$ s$^{-2}$'}

    hail_cols = dict(enumerate(colours))
    _, axs = plt.subplots(ncols=2, nrows=7, figsize=figsize, gridspec_kw={'hspace': 0.3, 'wspace': 0.05})

    for i, v in enumerate(plot_cols):
        sns.boxplot(
            stats_table,
            y=v,
            x='mp_scheme',
            ax=axs.flat[i],
            hue=hail_flag,
            width=0.5,
            legend=i == len(plot_cols) - 1,
            palette=hail_cols,
        )
        axs.flat[i].set_xlabel('')

        col = (i % 2) + 1
        row = (i // 2) + 1

        if row != len(plot_cols) / 2:
            axs.flat[i].set_xticks([])
        axs.flat[i].set_title(plot_cols[v])

        u = stats[v].attrs['units']
        axs.flat[i].set_ylabel(unit_renamer.get(u, u))

        if col == 2:  # noqa: PLR2004
            axs.flat[i].yaxis.tick_right()
            axs.flat[i].yaxis.set_label_position('right')

    sns.move_legend(axs.flat[i], 'center', bbox_to_anchor=(0, -0.75), title=f'Surface hail ({hail_indicator})')

    if file is not None:
        plt.savefig(file, dpi=300, bbox_inches='tight')

    plt.show()


def plot_surface_hailsizes(spatial_maxes, figsize=(6, 4), file=None, damaging_threshold=20, renamer=None, width=0.7):
    """Plot a comparison of surface hail sizes using HAILCAST vs microphysics schemes.

    Args:
        spatial_maxes: Spatial maxima including hail_maxk1 and hailcast_diam_max.
        figsize: Figure size. Defaults to (6,4).
        file: Plot to this (optional) file.
        damaging_threshold: Damaging hail threshold in mm.
        renamer: Rename variables?
        width: Width for bars.

    """
    if renamer is None:
        renamer = {'hail_maxk1': 'Microphysics', 'hailcast_diam_max': 'HAILCAST'}

    surface_hailsizes = spatial_maxes[['hail_maxk1', 'hailcast_diam_max']].to_dataframe().reset_index()
    surface_hailsizes['hail_maxk1'] = surface_hailsizes['hail_maxk1']
    surface_hailsizes['hail_maxk1'] = surface_hailsizes['hail_maxk1'].where(surface_hailsizes['hail_maxk1'] > 0)
    surface_hailsizes['hailcast_diam_max'] = surface_hailsizes['hailcast_diam_max'].where(surface_hailsizes['hailcast_diam_max'] > 0)

    # True/False when hailcast or MP scheme shows damaging hail.
    damaging_occurrences = surface_hailsizes[['domain', 'mp_scheme', 'event', 'hailcast_diam_max', 'hail_maxk1']].copy()
    damaging_occurrences['any_hail_hailcast_diam_max'] = damaging_occurrences['hailcast_diam_max'] >= 0
    damaging_occurrences['any_hail_hail_maxk1'] = damaging_occurrences['hail_maxk1'] >= 0
    damaging_occurrences['hailcast_diam_max'] = damaging_occurrences['hailcast_diam_max'] >= damaging_threshold
    damaging_occurrences['hail_maxk1'] = damaging_occurrences['hail_maxk1'] >= damaging_threshold
    damaging_events = (damaging_occurrences.groupby(['domain', 'mp_scheme', 'event']).sum() > 0).groupby(['domain', 'mp_scheme']).sum().reset_index()

    surface_hailsizes = surface_hailsizes.dropna(how='all', subset=['hail_maxk1', 'hailcast_diam_max'])
    surface_hailsizes = surface_hailsizes.rename(columns=renamer)
    surface_hailsizes = surface_hailsizes.melt(id_vars=['timestep', 'event', 'domain', 'mp_scheme'])

    colors = ['#E69F00', '#56B4E9', '#009E73', '#F0E442']
    g = sns.catplot(
        data=surface_hailsizes,
        kind='box',
        x='variable',
        y='value',
        hue='mp_scheme',
        col='domain',
        palette=colors,
        width=width,
    )
    g.set_axis_labels('', 'Hail diameter [mm]')
    g.legend.set_title('MP scheme')
    g.fig.set_size_inches(10, 2.5)
    g.set_titles('{col_name}')
    g.set(ylim=(-20, surface_hailsizes.value.max()*1.1))

    numbars = len(spatial_maxes.mp_scheme.values)
    for ax, d in zip(g.axes.flat, surface_hailsizes['domain'].unique()):
        for j, x in enumerate(renamer):
            from_x = j - 0.5 * width
            for i, mp in enumerate(spatial_maxes.mp_scheme.values):
                offset = i * width / numbars + (width / numbars / 2)
                txt = damaging_events.loc[
                        (damaging_events['mp_scheme'] == mp) &
                        (damaging_events['domain'] == d), x].iloc[0]
                any_txt = damaging_events.loc[
                        (damaging_events['mp_scheme'] == mp) &
                        (damaging_events['domain'] == d), f'any_hail_{x}'].iloc[0]
                if any_txt != 0:
                    ax.text(x=from_x + offset, y=-15, ha='center', s=txt)

    if file is not None:
        plt.savefig(file, dpi=300, bbox_inches='tight')

    plt.show()

    hailcast_cases = int(
        (spatial_maxes.sel(mp_scheme=['MY2', 'NSSL', 'Thompson'], domain='1 km').hailcast_diam_max.max('timestep') >= damaging_threshold).sum().values,
    )
    mp_cases = int((spatial_maxes.sel(mp_scheme=['MY2', 'NSSL', 'Thompson'], domain='1 km').hail_maxk1.max('timestep') >= damaging_threshold).sum().values)

    return hailcast_cases, mp_cases


def confusion_matrix(
    dat,
    hailcast='event_includes_hail_hailcast',
    micro='event_includes_hail_micro',
    figsize=(12, 3.5),
    file=None,
):
    """Plot and return confusion matrices by MP scheme and domain."""
    rows = []

    for dd in dat.domain.values:
        for mp in ['All', *list(np.unique(dat.mp_scheme))]:
            d = dat.sel(domain=dd) if mp == 'All' else dat.sel(mp_scheme=mp, domain=dd)

            H_M = int(np.sum(np.logical_and(d[hailcast], d[micro])))  # noqa: N806
            NH_M = int(np.sum(np.logical_and(~d[hailcast], d[micro])))  # noqa: N806
            H_NM = int(np.sum(np.logical_and(d[hailcast], ~d[micro])))  # noqa: N806
            NH_NM = int(np.sum(np.logical_and(~d[hailcast], ~d[micro])))  # noqa: N806

            rows.append(pd.DataFrame({'domain': [dd], 'scheme': [mp], 'hailcast': True, 'micro': True, 'n': H_M}))
            rows.append(pd.DataFrame({'domain': [dd], 'scheme': [mp], 'hailcast': False, 'micro': True, 'n': NH_M}))
            rows.append(pd.DataFrame({'domain': [dd], 'scheme': [mp], 'hailcast': True, 'micro': False, 'n': H_NM}))
            rows.append(pd.DataFrame({'domain': [dd], 'scheme': [mp], 'hailcast': False, 'micro': False, 'n': NH_NM}))

    con = pd.concat(rows)

    g = sns.FacetGrid(con, col='scheme', row='domain', sharex=True, sharey=True)

    def draw_heatmap(data, **kwargs):  # noqa: ARG001
        table = data.pivot(index='hailcast', columns='micro', values='n')

        total = table.values.sum()
        pct = 100 * table / total
        annot = table.astype(str) + '\n(' + pct.round(0).astype(int).astype(str) + '%)'

        ax = sns.heatmap(table, annot=annot, fmt='', cmap='Blues', cbar=False, square=True, linewidths=0.5, linecolor='black')
        ax.set_xlabel('Microphysics')
        ax.set_ylabel('HAILCAST')

        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(1)
            spine.set_edgecolor('black')

    g.map_dataframe(draw_heatmap)
    g.set_titles(row_template='{row_name}', col_template='{col_name}')
    g.fig.set_size_inches(figsize)

    plt.tight_layout()
    if file is not None:
        plt.savefig(file, dpi=300, bbox_inches='tight')

    plt.show()
    return con
