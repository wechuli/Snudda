"""
Creates param files for spn's including parameters for dopamine modulation
"""

import json
import numpy as np
import h5py

                

# fixed values for ca (if random missing)
fixed_ca_factors = {'ispn':[0.7, 0.7, 0.95, 0.7], 
                    'dspn':[1.3, 1.3, 0.5] }


# suffix of modulated ion channels per cell type
suffix      = { 'ispn':[ 'kir', 'kas', 'kaf', 'naf', 'cal12', 'cal13', 'can', 'car' ],
                'dspn':[ 'kir', 'kas', 'kaf', 'naf', 'cal12', 'cal13', 'can' ]      }

compartment = { 'naf':  ['somatic','basal','axonal'],
                'kas':  ['somatic','basal','axonal'],
                'kaf':  ['somatic','basal'],
                'kir':  ['somatic','basal'],
                'cal12':['somatic','basal'],
                'cal13':['somatic','basal'],
                'car':  ['somatic','basal'],
                'can':  ['somatic']                 }
                
                
for cell_type in ['ispn', 'dspn']:

    # open cell type specific library of mod factors
    if cell_type == 'dspn':
        tag = 'dspn_batch3'
    else:
        tag = cell_type
    lib_factors = h5py.File('modulation_factors/lib_modFactors_{}.h5'.format(tag), 'r')
        
    # open paramfile
    param_new = []
    
    for i in range(len(lib_factors)):
        raw_factors = lib_factors.get('factors_set{}'.format(i))
        raw_factors = np.array(raw_factors)
        param_temp  = []
        if len(raw_factors) == 4:
            raw_factors = list(raw_factors) + fixed_ca_factors[cell_type]
        for k,key in enumerate(suffix[cell_type]):
            for comp in compartment[key]:
                if cell_type == 'dspn' and comp == 'axonal': continue   # don't modulate axon in dspn
                param_temp.append( {
                                    "dist_type": "uniform", 
                                    "mech": "{}_ms".format(key), 
                                    "mech_param": "maxMod", 
                                    "param_name": "maxMod_{}_ms".format(key), 
                                    "sectionlist": comp, 
                                    "type": "range", 
                                    "value": raw_factors[k]
                                    })
        param_new.append( param_temp )
    
    # dump to file
    with open( '{}_modulation.json'.format(cell_type), 'w') as f:
        json.dump(param_new, f, indent=4)




