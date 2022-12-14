# Functions to help examine WRF metadata.

import xarray
import numpy as np

def analyse_wrfinput(wrfinput_file):
    """
    Print information to show basic setup options stored in a wrfinput file, and show summary plots of input profiles.
    
    Arguments:
        wrfinput_file: The file name to analyse.
        ideal: If true, check ideal-case assumptions.
        plot_f: Plot T, QV and P profiles.
        sounding_file: If specified, a sounding file to pass to plot_wrfinput_profiles().
    """
    
    wrfin = xarray.open_dataset(wrfinput_file)
    
    # Calculate total geopotential height (staggered).
    hgt = ((wrfin.PH + wrfin.PHB) / 9.81).isel(Time=0).mean(['south_north', 'west_east'])
    
    # Calculate difference in base-levels (mass-points).
    zdiffs = hgt.values[1:] - hgt.values[:-1]
    
    # Print important initialisation values.
    print('Sea surface temperature (SST):\t\t\t' + str(np.unique(wrfin.SST)[0]) + ' ' + wrfin.SST.attrs['units'])
    print('Surface skin temperature (TSK):\t\t\t' + str(np.unique(wrfin.TSK)[0]) + ' ' + wrfin.TSK.attrs['units'])
    print('Soil temperature at lower boundary (TMN):\t' + str(np.unique(wrfin.TMN)[0]) + ' ' + wrfin.TMN.attrs['units'])
    print('Horizontal grid spacing (DX):\t\t\t' + str(wrfin.DX) + ' m')
    print('Horizontal (S-N) grid spacing (DY):\t\t' + str(wrfin.DY) + ' m')
    print('Horizontal (W-E) domain size:\t\t\t' + str(wrfin.attrs['WEST-EAST_GRID_DIMENSION']-1) + ' mass points')
    print('Horizontal (S-N) domain size:\t\t\t' + str(wrfin.attrs['SOUTH-NORTH_GRID_DIMENSION']-1) + ' mass points')
    print('Vertical domain size:\t\t\t\t' + str(wrfin.attrs['BOTTOM-TOP_GRID_DIMENSION']-1) + ' mass points')
    print('Maximum geopotential height (model-top):\t' + str(np.round(hgt.max().values, 1)) + ' m')
    print('Min, mean, max vertical dist. between mass pts:\t' + str(np.round(np.min(zdiffs), 1)) + ', ' + 
          str(np.round(np.mean(zdiffs), 1)) + ', ' + str(np.round(np.max(zdiffs), 1)) + ' m')
    print('Model-top pressure:\t\t\t\t' + str(np.round(wrfin.P_TOP.isel(Time=0).data, 1)) + ' ' + wrfin.P_TOP.attrs['units'])
    print('Physics schemes:')
    print('\tMicrophysics:\t\t\t\t' + wrf_mp_scheme(wrfin))
    print('\tRadiation (longwave):\t\t\t' + wrf_ra_lw_scheme(wrfin))
    print('\tRadiation (shortwave):\t\t\t' + wrf_ra_sw_scheme(wrfin))
    print('\tSurface layer:\t\t\t\t' + wrf_sf_sfclay_scheme(wrfin))
    print('\tLand-surface:\t\t\t\t' + wrf_sf_surface_scheme(wrfin))
    print('\tPBL:\t\t\t\t\t' + wrf_pbl_scheme(wrfin))
    print('\tCumulus:\t\t\t\t' + wrf_cu_scheme(wrfin))
    print('Turbulence options:')
    print('\tDiffusion (diff_opt):\t\t\t' + wrf_diff_opt(wrfin))
    print('\tEddy coefficient (km_opt):\t\t' + wrf_km_opt(wrfin))

def wrf_mp_scheme(wrfin):
    """
    Lookup the microphysics scheme information in a wrfinput file and return a description string.
    
    Arguments:
        wrfin: The open wrfinput file as an xarray object.
    """
    
    schemes = {1:  'Kessler',
               2:  'Purdue Lin',
               3:  'WSM3',
               4:  'WSM5',
               5:  'Eta (Ferrier)',
               6:  'WSM6',
               7:  'Goddard',
               8:  'Thompson',
               9:  'Milbrandt 2-moment',
               10: 'Morrison 2-moment',
               11: 'CAM 5.1',
               13: 'SBU-YLin',
               14: 'WDM5',
               16: 'WDM6',
               17: 'NSSL 2-moment',
               18: 'NSSL 2-moment with CCN prediction',
               19: 'NSSL 1-moment',
               21: 'NSSL 1-moment lfo',
               22: 'NSSL 2-moment without hail',
               28: 'Thompson aerosol- aware',
               30: 'HUJI SBM fast',
               32: 'HUJI SBM full',
               40: 'Morrison+CESM aerosol',
               50: 'P3',
               51: 'P3 nc',
               52: 'P3 2ice',
               53: 'P3 3M'}
    
    return(str(wrfin.MP_PHYSICS) + ' (' + schemes[wrfin.MP_PHYSICS] + ')')

def wrf_ra_lw_scheme(wrfin):
    """
    Lookup the longwave radiation scheme information in a wrfinput file and return a description string.
    
    Arguments:
        wrfin: The open wrfinput file as an xarray object.
    """
    
    schemes = {1: 'RRTM',
               3: 'CAM',
               4: 'RRTMG',
               24: 'RRTMG fast',
               14: 'RRTMG-K',
               5: 'New Goddard',
               7: 'FLG',
               31: 'Held-Suarez',
               99: 'GFDL'}
        
    return(str(wrfin.RA_LW_PHYSICS) + ' (' + schemes[wrfin.RA_LW_PHYSICS] + ')')
          
def wrf_ra_sw_scheme(wrfin):
    """
    Lookup the shortwave radiation scheme information in a wrfinput file and return a description string.
    
    Arguments:
        wrfin: The open wrfinput file as an xarray object.
    """
    
    schemes = {1: 'Dudhia',
               2: 'Goddard',
               3: 'CAM',
               4: 'RRTMG',
               24: 'RRTMG',
               14: 'RRTMG-K',
               5: 'New Goddard',
               7: 'FLG',
               99: 'GFDL'}
        
    return(str(wrfin.RA_SW_PHYSICS) + ' (' + schemes[wrfin.RA_SW_PHYSICS] + ')')
        
def wrf_sf_sfclay_scheme(wrfin):
    """
    Lookup the surface layer scheme information in a wrfinput file and return a description string.
    
    Arguments:
        wrfin: The open wrfinput file as an xarray object.
    """
    
    schemes = {0: 'No surface-layer',
               1: 'Revised MM5 Monin-Obukhov',
               2: 'Monin-Obukhov (Janjic Eta)',
               3: 'NCEP GFS',
               4: 'QNSE',
               5: 'MYNN',
               7: 'Pleim-Xiu',
               91: 'Old MM5 surface layer'}
        
    return(str(wrfin.SF_SFCLAY_PHYSICS) + ' (' + schemes[wrfin.SF_SFCLAY_PHYSICS] + ')')
       
def wrf_sf_surface_scheme(wrfin):
    """
    Lookup the land-surface scheme information in a wrfinput file and return a description string.
    
    Arguments:
        wrfin: The open wrfinput file as an xarray object.
    """
    
    schemes = {0: 'No surface temp prediction',
               1: 'Thermal diffusion',
               2: 'Unified Noah',
               3: 'RUC',
               4: 'Noah-MP',
               5: 'CLM4',
               7: 'Pleim-Xiu',
               8: 'SSiB'}
        
    return(str(wrfin.SF_SURFACE_PHYSICS) + ' (' + schemes[wrfin.SF_SURFACE_PHYSICS] + ')')   

def wrf_diff_opt(wrfin):
    """
    Report the diff_opt value in the wrfinput file. 
    
    Arguments:
        wrfin: The open wrfinput file as an xarray object.
    """
    
    schemes = {0: 'No turbulence',
               1: 'Simple diffusion',
               2: 'Full diffusion'}
    
    return(str(wrfin.DIFF_OPT) + ' (' + schemes[wrfin.DIFF_OPT] + ')') 

def wrf_km_opt(wrfin):
    """
    Report the km_opt value in the wrfinput file. 
    
    Arguments:
        wrfin: The open wrfinput file as an xarray object.
    """
    
    schemes = {1: 'Constant K',
               2: '3D TKE',
               3: '3D Smagorinsky',
               4: '2D (horiz) Smagorinsky'}
    
    return(str(wrfin.KM_OPT) + ' (' + schemes[wrfin.KM_OPT] + ')')

def wrf_pbl_scheme(wrfin):
    """
    Lookup the PBL scheme information in a wrfinput file and return a description string.
    
    Arguments:
        wrfin: The open wrfinput file as an xarray object.
    """
    
    schemes = {0: 'No PBL scheme',
               1: 'YSU',
               2: 'MYJ',
               3: 'GFS (hwrf)',
               4: 'QNSE-EDMF',
               5: 'MYNN2',
               6: 'MYNN3',
               7: 'ACM2',
               8: 'BouLac',
               9: 'UW',
               10: 'TEMF',
               11: 'Shin-Hong',
               12: 'GBM',
               99: 'MRF'}
        
    return(str(wrfin.BL_PBL_PHYSICS) + ' (' + schemes[wrfin.BL_PBL_PHYSICS] + ')') 

def wrf_cu_scheme(wrfin):
    """
    Lookup the cumulus scheme information in a wrfinput file and return a description string.
    
    Arguments:
        wrfin: The open wrfinput file as an xarray object.
    """
    
    schemes = {0: 'No cumulus parameterisation',
               1: 'Kain-Fritsch (new Eta)',
               2: 'Betts-Miller-Janjic',
               3: 'Grell-Freitas',
               4: 'Scale-aware GFS Simplified Arakawa-Schubert (SAS)',
               5: 'New Grell (G3)',
               6: 'Tiedtke',
               7: 'Zhang-McFarlane from CESM',
               10: 'Modified Kain-Fritsch',
               11: 'Multi-scale Kain-Fritsch',
               14: 'New GFS SAS from YSU',
               16: 'A newer Tiedke',
               93: 'Grell-Devenyi ensemble',
               94: '2015 GFS Simplified Arakawa-Schubert (HWRF)',
               95: 'Previous GFS Simplified Arakawa-Schubert (HWRF)',
               99: 'Previous Kain-Fritsch'}
        
    return(str(wrfin.CU_PHYSICS) + ' (' + schemes[wrfin.CU_PHYSICS] + ')')  

def wrf_shcu_scheme(wrfin):
    """
    Lookup the shallow cumulus scheme information in a wrfinput file and return a description string.
    
    Arguments:
        wrfin: The open wrfinput file as an xarray object.
    """
    
    schemes = {0: 'No independent shallow cumulus',
               2: 'Park and Bretherton from CAM5',
               3: 'GRIMS'}
        
    return(str(wrfin.SHCU_PHYSICS) + ' (' + schemes[wrfin.SHCU_PHYSICS] + ')')  

def true_false(v):
    """
    Return 'true' if v != 0 and 'false' if v == 0.
    """

    if v == 0:
        return('False')
    else:
        return('True')
    
