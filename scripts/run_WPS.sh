#!/bin/bash
# Run WPS to prepare a WRF run.

#PBS -q normal
#PBS -P w42
#PBS -l storage=gdata/up6+gdata/hh5+gdata/rt52+gdata/zz93+gdata/sx70
#PBS -l ncpus=8
#PBS -l walltime=00:10:00
#PBS -l mem=192GB
#PBS -j oe
#PBS -W umask=0022
#PBS -l wd
#PBS -l jobfs=1GB
#PBS -N WPS_job

module use /g/data3/hh5/public/modules
module load conda/analysis3-unstable

# Run geogrid.
geogrid/geogrid.exe

# Prepare ERA5 data into a GRIB file.
era5grib wrf --namelist namelist.wps --geo geo_em.d01.nc --output GRIBFILE.AAA

# Run ungrib to extract GRIB data.
ungrib/ungrib.exe 

# Run metgrid to interpolate input data.
metgrid/metgrid.exe