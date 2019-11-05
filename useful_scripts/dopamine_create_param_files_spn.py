"""
Creates param files for spn's including parameters for dopamine modulation
"""

import json
import numpy as np
import h5py

    
model_specs =   {'dspn': {
                    'name'  :[  'str-dspn-e150602_c1_D1-mWT-0728MSN01-v20190508',
                                'str-dspn-e150917_c6_D1-m21-6-DE-v20190503',
                                'str-dspn-e150917_c9_d1-mWT-1215MSN03-v20190521',
                                'str-dspn-e150917_c10_D1-mWT-P270-20-v20190521' ],
                    'id'    :  [5,7,2,2] },
                 'ispn': {
                    'name'  :[  'str-ispn-e150908_c4_D2-m51-5-DE-v20190611',
                                'str-ispn-e150917_c11_D2-mWT-MSN1-v20190603',
                                'str-ispn-e151123_c1_D2-mWT-P270-09-v20190527',
                                'str-ispn-e160118_c10_D2-m46-3-DE-v20190529' ],
                    'id'    :  [7,2,2,4] }
                }
                

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
    lib_factors = h5py.File('modulation_factors/lib_modFactors_{}.h5'.format(cell_type), 'r')
     
    for model in model_specs[cell_type]['name']:               
        
        # open paramfile
        param_org = json.load(open( './cellspecs/{}/{}/parameters.json'.format(cell_type,model) ))
        param_new = []
        
        for i in range(len(lib_factors)):
            raw_factors = lib_factors.get('factors_set{}'.format(i))
            raw_factors = np.array(raw_factors)
            param_temp  = param_org.copy()
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
        with open( './cellspecs/{}/{}/parameters_with_modulation.json'.format(cell_type, model), 'w') as f:
            json.dump(param_new, f, indent=4)




