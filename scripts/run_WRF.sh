#!/bin/bash

#PBS -q normal
#PBS -P li18
#PBS -l storage=gdata/li18
#PBS -l walltime=06:00:00
#PBS -l mem=96GB       
#PBS -l ncpus=48
#PBS -j oe
#PBS -l wd
#PBS -W umask=0022
#PBS -N WRF_job

# qsub -I -q normal -P li18 -l storage=gdata/li18 -l walltime=06:00:00 -l mem=96GB -l ncpus=48 -j oe -l wd -W umask=0022 -N WRF_job

module load intel-compiler/2019.3.199
module load openmpi/4.0.2
module load ncl/6.6.2
module load hdf5/1.10.5
module load netcdf/4.7.1
module load python3/3.12.1

ulimit -s unlimited

echo 'Running in directory:' `pwd`
env > run_environment_real.txt

# Link WPS output files to currect directory.
echo 'Linking met_em files...'
ln -sf ../../WPS/met_em* .

echo "Running wrf.exe using $PBS_NCPUS mpi nodes..."
time mpirun -np $PBS_NCPUS -report-bindings ./real.exe 
mv rsl.error.0000 real.error

echo "Running wrf.exe using $PBS_NCPUS mpi nodes..."
time mpirun -np $PBS_NCPUS -report-bindings ./wrf.exe
