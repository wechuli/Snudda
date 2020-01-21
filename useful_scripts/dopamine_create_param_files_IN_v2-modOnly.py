"""
Creates param files for spn's including parameters for dopamine modulation
"""

import json
import numpy as np
import h5py

    
model_specs =   {'fs': {
                    'name'  :[  'str-fs-e160628_FS2-mMTC180800A-IDB-v20190226',
                                'str-fs-e161024_FS16-mDR-rat-Mar-13-08-1-536-R-v20190225',
                                'str-fs-e161205_FS1-mMTC180800A-IDB-v20190312',
                                'str-fs-e180418_FS5-mMTC251001A-IDB-v20190301' ],
                    'id'    :  [2,2,1,0] },
                 'chin': {
                    'name'  :  [ 'str-chin-e170614_cell6-m17JUL301751_170614_no6_MD_cell_1_x63-v20190710' ],
                    'id'    :  [ 8 ] },
                 'lts': {
                    'name'  :  [ 'LTS_Experiment-9862_20181211' ],
                    'id'    :  [ 0 ] }
                }


# suffix of modulated ion channels per cell type
suffix      = { 'fs':   ['kir', 'kas', 'kaf', 'naf'],
                'chin': ['na','na2','kv4','kir2','hcn12','cap'],
                'lts':  ['na3','hd']     }
             
                
for cell_type in ['fs', 'chin', 'lts']:
    
    if cell_type == 'chin': ct = 'ch'
    else: ct = cell_type

    # open cell type specific library of mod factors
    lib_factors = h5py.File('modulation_factors/lib_modFactors_{}.h5'.format(cell_type), 'r')
     
    model = model_specs[cell_type]['name'][0]               
        
    # open paramfile
    param_org = json.load(open( '../cellspecs/{}/{}/parameters.json'.format(cell_type,model) ))
    param_new = []
    param_temp = []
    
    for i in range(len(lib_factors)):
        raw_factors = lib_factors.get('factors_set{}'.format(i))
        raw_factors = np.array(raw_factors)
        print(raw_factors)
        flag = 0
        
        # loop over params in org
        for par in param_org:
            split = par["param_name"].split('_')
            if len(split) > 1: name = split[1]; parameter = split[0]
            else: continue
            if 'mech_param' in par: 
                if par['mech_param'] == 'q': continue
            elif not parameter in ['gbar', 'gmax', 'pbar']: continue
            # check if the param is modulated by da?
            for k,key in enumerate(suffix[cell_type]):
                if name == key:
                    comp = par["sectionlist"]
                    param_temp.append( {
                                        "dist_type": "uniform", 
                                        "mech": "{}_{}".format(name,ct), 
                                        "mech_param": "maxMod", 
                                        "param_name": "maxMod_{}_{}".format(name,ct), 
                                        "sectionlist": comp, 
                                        "type": "range", 
                                        "value": raw_factors[k]
                                        })
                    break
                
            
        param_new.append(param_temp)
    # dump to file
    with open( '{}_modulation.json'.format(cell_type), 'w') as f:
        json.dump(param_new, f, indent=4)




