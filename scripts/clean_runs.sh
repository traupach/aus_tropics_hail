#!/bin/bash
# Clean up run directories after running; remove symlinks to WRF executables etc. 
# Run from the base output directory, ie /g/data/li18/tr2908/kimberley_hail/WRF_v4.6.0/simulations.

find . -type l -name 'aerosol*' -exec rm {} +
find . -type l -name 'BROADBAND*' -exec rm {} +
find . -type l -name 'bulkdens*' -exec rm {} +
find . -type l -name 'CAM*' -exec rm {} +
find . -type l -name 'co2*' -exec rm {} +
find . -type l -name 'capacity*' -exec rm {} +
find . -type l -name 'bulk*' -exec rm {} +
find . -type l -name 'CCN*' -exec rm {} +
find . -type l -name 'CLM*' -exec rm {} +
find . -type l -name 'const*' -exec rm {} +
find . -type l -name 'ecl*' -exec rm {} +
find . -type l -name 'ETAM*' -exec rm {} +
find . -type l -name 'GEN*' -exec rm {} +
find . -type l -name 'grib*' -exec rm {} +
find . -type l -name 'HLC*' -exec rm {} +
find . -type l -name 'ish*' -exec rm {} +
find . -type l -name 'kern*' -exec rm {} +
find . -type l -name 'LAND*' -exec rm {} +
find . -type l -name 'mass*' -exec rm {} +
find . -type l -name '*.exe' -exec rm {} +
find . -type l -name 'MP*' -exec rm {} +
find . -type l -name 'p3*' -exec rm {} +
find . -type l -name 'README*' -exec rm {} +
find . -type l -name 'RRTM*' -exec rm {} +
find . -type l -name 'run*' -exec rm {} +
find . -type l -name 'ozone*' -exec rm {} +
find . -type l -name 'SOIL*' -exec rm {} +
find . -type l -name 'STO*' -exec rm {} +
find . -type l -name 'term*' -exec rm {} +
find . -type l -name 'tr*' -exec rm {} +
find . -type l -name 'URB*' -exec rm {} +
find . -type l -name 'VEG*' -exec rm {} +
find . -type l -name 'wind*' -exec rm {} +
