"""Use xarray_parcel to calculate convective properties for basic_params* files in the current directory to conv_properties_*.nc."""

import sys
from pathlib import Path

sys.path.append(Path('~/git/xarray_parcel/').expanduser())

from glob import glob

import modules.parcel_functions as parcel
import xarray

parcel.load_moist_adiabat_lookups(base_dir='~/')

files = sorted(glob('basic_params*.nc'))
for filename in files:
    dat = xarray.open_dataset(filename)
    dat = dat.load()
    dat = dat.chunk({'time': 1, 'bottom_top': -1, 'west_east': -1, 'south_north': -1})
    dat = dat.rename({'z': 'height_asl', 'u': 'wind_u', 'v': 'wind_v'})
    dat['surface_wind_u'] = dat.wind_u.isel(bottom_top=0)
    dat['surface_wind_v'] = dat.wind_v.isel(bottom_top=0)
    dat['wind_height_above_surface'] = dat.z_agl

    conv = parcel.min_conv_properties(dat=dat, vert_dim='bottom_top')
    outfile = filename.replace('basic_', 'conv_')
    comp = {'zlib': True, 'shuffle': True, 'complevel': 5}
    encoding = {var: comp for var in conv.data_vars}
    conv.to_netcdf(outfile, encoding=encoding)
    del dat, conv
