import math
import os  # noqa: D100
import shutil

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import xarray
from matplotlib import gridspec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon
from matplotlib.ticker import MaxNLocator, ScalarFormatter
from metpy.plots import SkewT
from metpy.units import units
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from cartopy.mpl.geoaxes import GeoAxes


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


def open_kimberley_data(hail_detections, sims_dir, mps=None, basic=True, conv=True, interp=True):
    """Open the data for the Kimberley hail experiments.

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
                event_basic = event_basic[['hailcast_diam_max', 'latitude', 'longitude']]

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


def circle_points(x, y, r, n, i):
    angle = 2 * math.pi * i / n  # angle in radians
    px = x + r * math.cos(angle)
    py = y + r * math.sin(angle)
    return px, py


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

    sns.move_legend(ax, 'upper left', bbox_to_anchor=(1, 1))

    # Add inset globe to show map location.
    inset_ax = inset_axes(
        ax,
        width=1.5,
        height=1.5,
        loc='center left',
        bbox_to_anchor=(0.975, 0.22),
        bbox_transform=ax.transAxes,
        borderpad=2,
        axes_class=GeoAxes,
        axes_kwargs={'projection': ccrs.NearsidePerspective(central_longitude=135, central_latitude=-25, satellite_height=35785831/5)},
    )
    inset_ax.add_feature(cfeature.LAND, zorder=0)
    inset_ax.add_feature(cfeature.OCEAN, zorder=0)
    inset_ax.add_feature(cfeature.COASTLINE)

    # Define the extent box as a list of (lon, lat) tuples
    extent_box = [
        (xlim[0], ylim[0]),
        (xlim[1], ylim[0]),
        (xlim[1], ylim[1]),
        (xlim[0], ylim[1]),
        (xlim[0], ylim[0])
    ]

    # Patch to highlight plotted region.
    patch = Polygon(extent_box, closed=True,
                    transform=ccrs.PlateCarree(),
                    facecolor='red', edgecolor='black', linewidth=0.2, alpha=0.7)
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

    """
    means = dat.isel(timestep=time_slice).to_dataframe().reset_index().groupby(['mp_scheme', 'pressure_level', 'event_includes_hail']).mean()
    sds = dat.isel(timestep=time_slice).to_dataframe().reset_index().groupby(['mp_scheme', 'pressure_level', 'event_includes_hail']).std()

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

    mps = stats['mp_scheme'].unique()
    fig, axs = plt.subplots(ncols=len(variables), nrows=len(mps), figsize=figsize, gridspec_kw={'wspace': wspace, 'hspace': hspace})

    for m, mp in enumerate(mps):
        for i, v in enumerate(variables):
            s = stats[np.logical_and(stats['variable'] == v, stats['mp_scheme'] == mp)]

            if np.all(np.isnan(s['mean'])):
                axs[m, i].set_visible(False)
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
            axs[m, i].xaxis.set_major_locator(MaxNLocator(nbins=3))

            axs[m, i].set_title(mp)

    legend_elements = [
        Line2D([0], [0], color=hail_colour, label='Hail-event profile'),
        Patch(facecolor=hail_colour, label='Hail-event std. dev. range', alpha=0.5),
        Line2D([0], [0], color=nohail_colour, label='No-hail-event profile'),
        Patch(facecolor=nohail_colour, label='No-hail-event std. dev. range', alpha=0.5),
    ]

    fig.legend(handles=legend_elements, loc='lower center', fontsize='small', bbox_to_anchor=(0.5, -0.05))

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
        Line2D([0], [0], color=hail_colour, label='H temperature'),
        Line2D([0], [0], color=hail_colour, linestyle='--', label='H dewpoint'),
        Patch(facecolor=hail_colour, label='H std. dev. range', alpha=alpha),
        Line2D([0], [0], color=nohail_colour, label='NH temperature'),
        Line2D([0], [0], color=nohail_colour, linestyle='--', label='NH dewpoint'),
        Patch(facecolor=nohail_colour, label='NH std. dev. range', alpha=alpha),
    ]

    legend_ax = fig.add_subplot(gs[len(mps) : len(mps) + 1])
    legend_ax.axis('off')
    legend_ax.legend(handles=legend_elements, loc='center', fontsize='small')

    if file is not None:
        plt.savefig(file, dpi=300, bbox_inches='tight')

    plt.show()
