# Example:
#
# python3 Network_plot_spike_raster.py save/traces/network-output-spikes-0.txt save/network-connect-synapse-file-0.hdf5


import json, glob
import numpy as np
import matplotlib.pyplot as plt

cell_types = ['iSPN', 'dSPN', 'FSN', 'LTS', 'ChIN']
types      = ['allInh', 'noFF', 'noLts', 'noLat']
legend     = ['control', 'FS', 'LTS', 'SPN']
ncells     = {'ChIN':133, 'LTS':71, 'FSN':133, 'dSPN':4842, 'iSPN':4842}
colors     = ['k','#e41a1c','#4daf4a','#377eb8']
ls         = ['--', '-', '-', '-']

fig,ax = plt.subplots(2, 1, figsize=(6,4))
f2,a2  = plt.subplots(3, 1, figsize=(6,6))

AX = []
for A in [ax,a2]:
    for a in A:
        AX.append(a)

# TODO update to time on x-axis and freq on y-axis

for j in [1,2,3,0]:
    t = types[j]
    files = glob.glob('networks/Skynet10000/figs/*{}*.json'.format(t))
    with open(files[0],'r') as f:
        data = json.load(f)
    for i,ct in enumerate(cell_types):
        
        AX[i].plot([x*2.3/100 for x in range(len(data[ct]['n']))], np.divide(data[ct]['n'],ncells[ct]*23*1e-3), label=legend[j], c=colors[j], ls=ls[j], lw=2)

for i,ct in enumerate(cell_types[:2]):
    #AX[i].plot([0,1.8], [0,0],  'k', lw=2)
    y2=10-i*5
    AX[i].plot([0,0],[0,y2],    'k', lw=2)
    AX[i].plot([0,0.02], [int(y2),int(y2)], 'k', lw=2)
    AX[i].plot([0,0.02], [0,0], 'k', lw=2)
    AX[i].set_ylabel(ct)
    AX[i].set_xlim([-0.1,1.8])
    AX[i].axis('off')
        
ax[0].legend(loc=1)

fig.savefig('preliminary_inhibition_network.png', dpi=600,transparent=True)

plt.show()
        
        

