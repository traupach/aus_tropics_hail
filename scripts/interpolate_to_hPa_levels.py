"""Use xarray_parcel to interpolate variables in basic_params* files in the current directory to pressure levels, and write pressure_level_*.nc."""

import sys
from pathlib import Path

sys.path.append(str(Path('~/git/xarray_parcel/').expanduser()))

from glob import glob

import modules.parcel_functions as parcel
import numpy as np
import xarray

parcel.load_moist_adiabat_lookups(base_dir='~/')
variables = ['pressure', 'temperature', 'rh', 'u', 'v', 'w', 'z', 'z_agl', 'dbz', 'td',
             'specific_humidity', 'qvapor', 'qcloud', 'qrain', 'qice', 'qhail', 'qnhail', 
             'qvhail', 'qgraupel', 'qngraupel', 'qvgraupel', 'qgraup']

files = sorted(glob('basic_params*.nc'))
for filename in files:
    dat = xarray.open_dataset(filename)
    dat = dat.load()
    dat = dat.chunk({'time': 1, 'bottom_top': -1, 'west_east': -1, 'south_north': -1})

    # Select only variables with bottom_top coordinates.
    vs = [x for x in variables if x in dat]
    dat = dat[vs]
    levels = []

    # Loop through pressure levels and interpolate to each using log(pressure) as the vertical coordinate.
    for p in np.arange(1000, 100, step=-50):
        level = parcel.log_interp(x=dat, coords=dat.pressure, at=p, dim='bottom_top')
        level = level.expand_dims({'pressure_level': [p]})
        levels.append(level)

    levels = xarray.merge(levels)
    levels.pressure_level.attrs['long_name'] = 'Interpolated pressure level'
    levels.pressure_level.attrs['units'] = 'hPa'

    # Copy attributes and add note.
    for v in vs:
        levels[v].attrs = dat[v].attrs
        levels[v].attrs['note'] = 'Interpolated using xarray_parcel log_interp to pressure levels'

    outfile = filename.replace('basic_', 'pressure_level_')
    comp = {'zlib': True, 'shuffle': True, 'complevel': 5}
    encoding = {var: comp for var in levels.data_vars}
    levels.to_netcdf(outfile)
    del dat
