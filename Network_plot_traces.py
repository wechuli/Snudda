# python3 Network_plot_traces.py save/traces/network-voltage-0.csv save/network-connect-synapse-file-0.hdf5


import sys, pickle
import os
import numpy as np
from snudda_load import SnuddaLoad
import re
import ntpath

class NetworkPlotTraces():

  ############################################################################
  
  def __init__(self,fileName,networkFile=None):
      
    self.fileName = fileName
    self.networkFile = networkFile

    self.time = []
    self.voltage = []

    self.readCSV()

    try:
      self.ID = int(re.findall('\d+', ntpath.basename(fileName))[0])
    except:
      print("Unable to guess ID, using 666.")
      self.ID = 666

    if(self.networkFile is not None):
      self.networkInfo = SnuddaLoad(self.networkFile)
      # assert(int(self.ID) == int(self.networkInfo.data["SlurmID"]))
   
    else:
      self.networkInfo = None
    

  ############################################################################
    
  def readCSV(self):

    data = np.genfromtxt(self.fileName, delimiter=',')

    assert(data[0,0] == -1) # First column should be time

    self.time = data[0,1:] / 1e3

    self.voltage = np.zeros((data.shape[0]-1,data.shape[1]-1))
    
    for rows in data[1:,:]:
      cID = int(rows[0])
      self.voltage[cID,:] = rows[1:] * 1e-3
            
  ############################################################################

  def plotTraces(self,traceID=None,offset=150e-3,colours=None,skipTime=None,
                 title=None, compare=0):

    if(skipTime is not None):
      print("!!! Excluding first " + str(skipTime) + "s from the plot")
    
    if(colours is None):
      colours = {"dSPN" : (77./255,151./255,1.0),
                 "iSPN" : (67./255,55./255,181./255),
                 "FSN" : (6./255,31./255,85./255),
                 "ChIN" : [252./255,102./255,0],
                 "LTS" : [150./255,63./255,212./255]}
    try:
    
      if(traceID is None):
        traceID = self.rowFromCellID.keys()
      
    except:
        import traceback
        tstr = traceback.format_exc()
        print(tstr)
        import pdb
        pdb.set_trace()
      
      
    
    print("Plotting traces: " + str(traceID))
    print("Plotted " + str(len(traceID)) + " traces (total " \
      + str(self.voltage.shape[0]) + ")")
      
    import matplotlib.pyplot as plt

    typesInPlot = set()
    
    if(self.networkInfo is not None):
      cellTypes = [n["type"] for n in self.networkInfo.data["neurons"]]
      cellIDcheck = [n["neuronID"] for n in self.networkInfo.data["neurons"]]
      try:
        assert (np.array([cellIDcheck[x] == x for x in traceID])).all(), \
          "Internal error, assume IDs ordered"
      except:
        import traceback
        tstr = traceback.format_exc()
        print(tstr)
        print("This is strange...")
        import pdb
        pdb.set_trace()
      
      cols = [colours[c] if c in colours else [0,0,0] for c in cellTypes]
    
    #import pdb
    #pdb.set_trace()
    
    fig = plt.figure()
    
    ofs = 0

    if(skipTime is not None):
      timeIdx = np.where(self.time >= skipTime)[0]
    else:
      skipTime = 0.0
      timeIdx = range(0,len(self.time))
      
    for r in traceID:

      typesInPlot.add(self.networkInfo.data["neurons"][r]["type"])
      
      if(colours is None or self.networkInfo is None):
        colour = "black"
      else:
        try:
          colour = cols[r]
        except:
          import traceback
          tstr = traceback.format_exc()
          print(tstr)
          import pdb
          pdb.set_trace()
          
      plt.plot(self.time,
               self.voltage[r,:] + ofs,
               color=colour,
               lw=3)
      ofs += offset
    
    if compare:
        path2control = '../Alex_model_repo/models/optim/Dopamine/Analysis/Results/'
        if title in ['iSPN', 'dSPN']:
            with open('{}{}_res_org.pkl'.format(path2control, title.lower()), 'rb') as f:
                ctrl = pickle.load(f)
        elif title == 'FSN':
            with open('{}fs_res_reorg.pkl'.format(path2control), 'rb') as f:
                ctrl = pickle.load(f) 
        elif title == 'ChIN':
            with open('{}chin_res_reorg.pkl'.format(path2control), 'rb') as f:
                ctrl = pickle.load(f)
        elif title == 'LTS':
            with open('{}lts_res_org.pkl'.format(path2control), 'rb') as f:
                ctrl = pickle.load(f)
        for cid in range(len(traceID)):
            #if title not in ['iSPN', 'dSPN', 'FSN', 'ChIN']: continue
            data = list(ctrl[0]['data'][cid]['control'].values())[0]
            plt.plot(np.array(data['t'])*1e-3,np.array(data['v'])*1e-3, '--k')
    plt.xlabel('Time')
    plt.ylabel('Voltage')

    if(title is not None):
      plt.title(title)
    
    if(offset != 0):
      ax = fig.axes[0]
      ax.set_yticklabels([])
    
    plt.tight_layout()
    plt.ion()
    plt.show()
    plt.draw()
    plt.pause(0.001)

    #plt.savefig('figures/Network-spikes-' + str(self.ID) + "-colour.pdf")

    
    if(len(typesInPlot) > 1):
      figName = 'figures/Network-spikes-' + str(self.ID) \
        + "-".join(typesInPlot) + "-DAtrans300colour.png"
    else:
      figName = 'figures/Network-spikes-' + str(self.ID) \
        + "-" + typesInPlot.pop() + "-colour.png"
      
    plt.savefig(figName,
                dpi=300)
    print("Saving to figure " + str(figName))


  ############################################################################

  def plotTraceNeuronType(self,neuronType,nTraces=10,offset=0,skipTime=0.0,compare=0):

    assert self.networkInfo is not None, "You need to specify networkInfo file"
    
    neuronTypes = [x["type"] for x in self.networkInfo.data["neurons"]]

    # Find numbers of the relevant neurons
    
    traceID = [x[0] for x in enumerate(neuronTypes) if x[1] == neuronType]
    
    nTraces = min(len(traceID),nTraces)

    if(nTraces <= 0):
      print("No traces of " + str(neuronType) + " to show")
      return
    
    self.plotTraces(offset=offset,traceID=traceID[:nTraces],skipTime=skipTime,
                    title=neuronType,compare=compare)
                                   
    
  ############################################################################
    
if __name__ == "__main__":

  if(len(sys.argv) > 1):
    fileName = sys.argv[1]

  if(len(sys.argv) > 2):
    networkFile = sys.argv[2]
  else:
    networkFile = None

  if(fileName is not None):
    npt = NetworkPlotTraces(fileName,networkFile)
    #npt.plotTraces(offset=0.2,traceID=[17,40,11,18])
    # npt.plotTraces(offset=0.2,traceID=[0,1,2,3,4,5,6,7,8,9])
    # npt.plotTraces(offset=0,traceID=[0,1,2,3,4,5,6,7,8,9])
    # npt.plotTraces(offset=0,traceID=[0,5,55]) #,5,55])
    #npt.plotTraces(offset=0,traceID=np.arange(0,100)) #,5,55])
    #npt.plotTraces(offset=-0.2,traceID=np.arange(0,20),skipTime=0.5)
    #npt.plotTraces(offset=-0.2,traceID=[5,54],skipTime=0.5)    
    #npt.plotTraces(offset=0.2,traceID=[1,5,7,15,16],skipTime=0.2)

    plotOffset = 0 # -0.2
    skipTime = 0 #0.5
    nTracesMax = 5
    comp=1
    npt.plotTraceNeuronType(neuronType="dSPN",nTraces=nTracesMax,offset=plotOffset,skipTime=skipTime,compare=comp)
    npt.plotTraceNeuronType(neuronType="iSPN",nTraces=nTracesMax,offset=plotOffset,skipTime=skipTime,compare=comp)
    npt.plotTraceNeuronType(neuronType="FSN",nTraces=nTracesMax,offset=plotOffset,skipTime=skipTime,compare=comp)
    npt.plotTraceNeuronType(neuronType="LTS",nTraces=nTracesMax,offset=plotOffset,skipTime=skipTime,compare=comp)
    npt.plotTraceNeuronType(neuronType="ChIN",nTraces=nTracesMax,offset=plotOffset,skipTime=skipTime,compare=comp)
    
    
    
  else:
    print("Usage: " + sys.argv[0] + " network-voltage-XXX.csv")
    
  import pdb
  pdb.set_trace()
