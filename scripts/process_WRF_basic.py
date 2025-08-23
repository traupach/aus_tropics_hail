"""Use wrf-python to extract basic properties from wrfout_d03 files in the current directory and write output files basic_properties_*.nc."""

import os
from glob import glob

import metpy.calc as mpcalc
import numpy as np
import wrf
import xarray
from netCDF4 import Dataset

files = sorted(glob('wrfout_d03*'))[-2:]
for filename in files:
    print(filename)
    nc = Dataset(filename)
    outfile = filename.replace('wrfout', 'basic_params') + '.nc'

    if os.path.exists(outfile):
        print(f'Skipping existing {outfile}...')
        continue

    dat = xarray.Dataset({'pressure': wrf.getvar(nc, 'pressure', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'temperature': wrf.getvar(nc, 'tk', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'rh': wrf.getvar(nc, 'rh', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'u': wrf.getvar(nc, 'ua', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'v': wrf.getvar(nc, 'va', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'w': wrf.getvar(nc, 'wa', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'z': wrf.getvar(nc, 'height', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'z_agl': wrf.getvar(nc, 'height_agl', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'ctt': wrf.getvar(nc, 'ctt', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'cloudfrac': wrf.getvar(nc, 'cloudfrac', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'dbz': wrf.getvar(nc, 'dbz', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'mdbz': wrf.getvar(nc, 'mdbz', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'pw': wrf.getvar(nc, 'pw', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'slp': wrf.getvar(nc, 'slp', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'ter': wrf.getvar(nc, 'ter', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'td': wrf.getvar(nc, 'td', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'updraft_helicity': wrf.getvar(nc, 'updraft_helicity', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'hailcast_diam_max': wrf.getvar(nc, 'HAILCAST_DIAM_MAX', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'hailnc': wrf.getvar(nc, 'HAILNC', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'graupelnc': wrf.getvar(nc, 'GRAUPELNC', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'hail_maxk1': wrf.getvar(nc, 'HAIL_MAXK1', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'hail_max2d': wrf.getvar(nc, 'HAIL_MAX2D', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'graupel_max': wrf.getvar(nc, 'GRPL_MAX', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'qvapour': wrf.getvar(nc, 'QVAPOR', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'qcloud': wrf.getvar(nc, 'QCLOUD', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'qrain': wrf.getvar(nc, 'QRAIN', timeidx=wrf.ALL_TIMES, squeeze=False),
                          'qice': wrf.getvar(nc, 'QICE', timeidx=wrf.ALL_TIMES, squeeze=False)})

    for var in ['QHAIL', 'QNGRAUPEL', 'QNHAIL', 'QVGRAUPEL', 'QVHAIL', 'QSNOW', 'QGRAUP', 'QIR', 'QIB']:
        if var in nc.variables:
            n = xarray.Dataset({var.lower(): wrf.getvar(nc, var, timeidx=wrf.ALL_TIMES, squeeze=False)})
            dat = xarray.merge([dat, n])
            del n

    assert not np.any(dat.pressure == dat.pressure.attrs['_FillValue'])
    assert not np.any(dat.pressure == dat.pressure.attrs['missing_value'])
    del dat.pressure.attrs['_FillValue']
    del dat.pressure.attrs['missing_value']

    dat['specific_humidity'] = mpcalc.specific_humidity_from_mixing_ratio(dat.qvapour).metpy.dequantify()
    dat = dat.rename({'Time': 'time', 'XLONG': 'longitude', 'XLAT': 'latitude'})
    dat = dat.reset_coords().drop_vars('XTIME')
    dat = dat.assign_coords({'south_north': dat.south_north,
                             'west_east': dat.west_east,
                             'bottom_top': dat.bottom_top})

    assert np.all(dat.ter == dat.ter.max('time')), 'Terrain is not constant.'
    dat['ter'] = dat.ter.max('time', keep_attrs=True)

    dat.attrs['projection'] = str(dat.u.attrs['projection'])

    for k in dat:
        if 'projection' in dat[k].attrs:
            del dat[k].attrs['projection']

    comp = {'zlib': True, 'shuffle': True, 'complevel': 5}
    encoding = {var: comp for var in dat.data_vars}
    dat.to_netcdf(outfile, encoding=encoding)
    del dat
