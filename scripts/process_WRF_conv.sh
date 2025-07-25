#!/bin/bash
# Calculate convective parameters from basic_params* files.

#PBS -q normal
#PBS -P li18
#PBS -l storage=gdata/li18+gdata/xp65
#PBS -l ncpus=28
#PBS -l walltime=00:15:00
#PBS -l mem=192GB
#PBS -j oe
#PBS -W umask=0022
#PBS -l wd
#PBS -l jobfs=1GB
#PBS -N process_WRF_conv_job

module use /g/data/xp65/public/modules
module load conda/analysis3-25.04

time python3 ~/git/kimberley_hail/scripts/process_WRF_conv.py
