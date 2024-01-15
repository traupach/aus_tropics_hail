#!/bin/bash
# Interpolate basic parameters to pressure levels.

#PBS -q normal
#PBS -P li18
#PBS -l storage=gdata/up6+gdata/hh5+gdata/w42
#PBS -l ncpus=28
#PBS -l walltime=00:15:00
#PBS -l mem=192GB
#PBS -j oe
#PBS -W umask=0022
#PBS -l wd
#PBS -l jobfs=1GB
#PBS -N interpolation_job

module use /g/data3/hh5/public/modules
module load conda/analysis3-22.04

time python3 ~/git/kimberley_hail/scripts/interpolate_to_hPa_levels.py
