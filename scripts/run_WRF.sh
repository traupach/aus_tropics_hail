#!/bin/bash

#PBS -q normal
#PBS -P w42
#PBS -l storage=gdata/up6+gdata/hh5
#PBS -l walltime=04:00:00
#PBS -l mem=96GB       
#PBS -l ncpus=48
#PBS -j oe
#PBS -l wd
#PBS -W umask=0022
#PBS -N WRF_job

module load openmpi
ulimit -s unlimited
limit stacksize unlimited

echo 'Running in directory:' `pwd`
env > run_environment_real.txt

# Link WPS output files to currect directory.
echo 'Linking met_em files...'
ln -sf ../../WPS/met_em* .

echo 'Running wrf.exe using $PBS_NCPUS mpi nodes...'
time mpirun -np $PBS_NCPUS -report-bindings ./real.exe 
mv rsl.error.0000 real.error

echo 'Running wrf.exe using $PBS_NCPUS mpi nodes...'
time mpirun -np $PBS_NCPUS -report-bindings ./wrf.exe
