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
                    'id'    :  [2,2,1,0] }
                }

     
for m,model in enumerate(model_specs['fs']['name']):               
    
    flag = 1
     
    # open files
    param_netw = json.load(open( 'cellspecs/fs/{}/parameters.json'.format(model) ))
    param_opt  = json.load(open( '../Alex_model_repo/models/optim/{}/config/parameters.json'.format(model) ))
    best_opt   = json.load(open( '../Alex_model_repo/models/optim/{}/best_models.json'.format(model) ))
    
    D = {}
    # loop over params in org
    for par in param_opt:
        name = par["param_name"]
        if 'bounds' in par:
            sl = par["sectionlist"]
            i = model_specs['fs']['id'][m]
            n2 = '{}.{}'.format(name,sl)
            val = best_opt[i][n2]
        else: val = par['value']
        if name in D: D[name]['org'].append(val); D[name]['full'].append(par)
        else: D[name] = {'org':[val], 'netw':[], 'full':[par]}
    for par in param_netw:
        name = par["param_name"]
        if 'fs' in name: name = name.replace('_fs', '')
        val = par['value']
        if val not in D[name]['org']: print(name, D[name]['org'], val); print(D[name]['full']); flag=0
        D[name]['netw'].append(val)
    
    '''
    for key in D:
        print(key,D[key]['org'],D[key]['netw'])
    print()'''
    
    if flag: print('model params of model:\n', model, '\nare identical\n') 



