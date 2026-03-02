#!/bin/bash
# Run WPS to prepare a WRF run.

#PBS -q normal
#PBS -P li18
#PBS -l storage=gdata/hh5+gdata/li18+gdata/rt52+gdata/zz93+gdata/sx70+gdata/xp65
#PBS -l ncpus=8
#PBS -l walltime=00:10:00
#PBS -l mem=192GB
#PBS -j oe
#PBS -W umask=0022
#PBS -l wd
#PBS -l jobfs=1GB
#PBS -N WPS_job

module load intel-compiler/2019.3.199
module load openmpi/4.0.2
module load ncl/6.6.2
module load hdf5/1.10.5
module load netcdf/4.7.1
module load python3/3.12.1

# Run geogrid.
./geogrid/geogrid.exe

# Prepare ERA5 data into a GRIB file.
module load conda/analysis3-26.01
~/.local/bin/era5grib wrf --era5land --namelist namelist.wps --geo geo_em.d01.nc --output GRIBFILE.AAA
module unload conda/analysis3-26.01

# Run ungrib to extract GRIB data.
./ungrib.exe 

# Run metgrid to interpolate input data.
./metgrid/metgrid.exe

# Remove temp files.
rm FILE*
rm GRIBFILE.AAA