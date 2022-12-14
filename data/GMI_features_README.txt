README for GPM Hail Events File

GPM GMI Identified Features and their estimated probabilities of severe hail based on Bang & Cecil (2019).

Features identified as contiguous areas anywhere within the GMI swath with an 
89 GHz Polarization Corrected Temperature at and below 200K.

Update 9/14/2021: this dataset has been updated to go from April 2014 to March 2022. 
The MERRA2 reanalysis dataset was used to calculate the Lapse Rate Tropopause (LRT)
height that was used to normalize the 37 GHz depression.

**CAVEAT**

In order to create a climatology, like the one seen in Bang and Cecil (2019) (Figure 7),
the “hail event” counts undergo some serious normalization in order to make a fair
comparison between high latitudes and the tropics, because of the satellite’s orbit.
A BIG word of caution if you want to use this event list to make your own climatology,
you will also need to perform overpass normalization, or your result will be biased towards
the higher latitudes where the sampling is denser. The sample sizes are not sufficient to 
prevent the appearance of noise (i.e, non-robust geographic patterns) when plotted at 
resolutions finer than a few degrees.  
**************

File Components:

YEAR, MONTH, DAY, HOUR, MIN : these are the time identifiers of the GPM overpass, in UTC time.
     
LAT : The latitude of the minimum 37 GHz PCT of the feature. 
      This is likely nearby the more intense part of the feature, 
      but is by no means the exact coordinate of the hail core. 
      One feature may have multiple hail cores, as the features 
      do not have an upper limit on their size.
  
LON : Longitude of the feature's minimum 37 GHz PCT    

P_hail_BC2019 : Probability of hail calculated using Normalized 37 GHz PCT Depression
                and [Histogram Adjusted] Minimum 19 GHz PCT. Minimum P_hail is 0%.  
                0 = 0%, 1 = 100%   

MIN10PCT : Feature-minimum 10GHz PCT. This is an emission channel but it *can* be scattered
   	   by extremely large hail.

MIN19PCT : Feature-minimum 19GHz PCT. This is a main component of the BC2019 algorithm.

MIN37PCT : Feature-minimum 37GHz PCT. Another major component of the BC2019 algorithm.

MIN85PCT : Feature-minimum 89 GHz PCT. (Called 85 GHZ because of TRMM legacy. Used 
	   to define feature boundary, and common precipitation frequency. 

DCFlag : "Deep Convection Flag" to screen for snow/surface features. Only values of 1
         were included in the Bang & Cecil 2019 climatology.
	 PCTFs with a [Max. 10 PCT - Min. 10 PCT]-[Max. 85 PCT - Min. 85 PCT] =< -30K
	 OR with a Min. 85 PCT =< 120K are given a DCflag of 1.   
         1 = keep 
         0 = exclude
