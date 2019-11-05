#!/usr/bin/env python3

# A wrapper script for the touch detection algorithm
#
# Usage:
#
# snudda init <networkPath> --size XXX
# -- Creates an a json config file
#
# snudda place <networkPath>
# -- Cell placement within volumes specified
#
# snudda detect <networkPath> [--hvsize hyperVoxelSize]
# -- Touch detection of putative synapses
#
# snudda prune <networkPath> [--mergeonly]
# -- Prune the synapses
#
# snudda input <networkPath> [--input yourInputConfig]
#
# snudda export <networkPath>
# -- Export to SONATA format (optional)
#
# snudda simulate <networkPath>
#
# snudda analyse <networkPath>
#
#
# snudda help me

# Johannes Hjorth, Royal Institute of Technology (KTH)
# Human Brain Project 2019

#
# This open source software code was developed in part or in whole in
# the Human Brain Project, funded from the European Union’s Horizon
# 2020 Framework Programme for Research and Innovation under Specific
# Grant Agreements No. 720270 and No. 785907 (Human Brain Project SGA1
# and SGA2).
#


import os
import sys
import timeit
import numpy as np
import zmq

class Snudda(object):

  ############################################################################
  
  def __init__(self,networkPath):

    if(networkPath[-1] == "/"):
      self.networkPath = networkPath[:-1]
    else:
      self.networkPath = networkPath
      
    # Add current dir to python path
    sys.path.append(os.getcwd())
    
    self.start = timeit.default_timer()

  ############################################################################

  def helpInfo(self,args):

    helpFile = "snudda_help.txt"
    os.path.exists(helpFile)

    with open(helpFile,"r") as f:
      for row in f:
        print(row,end="")
    
  
  ############################################################################
  
  def initConfig(self,args):
    # self.networkPath = args.path
    print("Creating config file")
    print("Network path: " + str(self.networkPath))

    assert args.size is not None, \
      "You need to speicfy --size when initialising config for network2"
    
    from CreateNetworkConfig import CreateNetworkConfig
    structDef = { "Striatum" : args.size,
                  "GPe" : 0,
                  "GPi" : 0,
                  "SNr" : 0,
                  "STN" : 0,
                  "Cortex" : 0,
                  "Thalamus" : 0}
    # Cortex and thalamus axons disabled right now, set to 1 to include one

    assert not os.path.exists(self.networkPath), \
      "Network path " + str(self.networkPath) + " already exists"

    if not os.path.exists(self.networkPath):
      os.makedirs(self.networkPath)

    nChannels = args.nchannels
      
    configFile = self.networkPath + "/network-config.json"
    CreateNetworkConfig(structDef=structDef,
                        configName=configFile,
                        nChannels=nChannels)

    if(args.size > 1e5):
      print("Make sure there is enough disk space in " + str(self.networkPath))
      print("Large networks take up ALOT of space")

    
  ############################################################################

  def placeNeurons(self,args):
    # self.networkPath = args.path
    print("Placing neurons")
    print("Network path: " + str(self.networkPath))    


    configFile = self.networkPath + "/network-config.json"
    positionFile = self.networkPath + "/network-neuron-positions.hdf5"
    logFileName = self.networkPath + "/logFile-place-neurons.txt"

    self.setupLogFile(logFileName) # sets self.logFile
    self.setupParallel() # sets self.dView and self.lbView

    import Network_place_neurons

    if(args.h5legacy):
      h5libver = "earliest"
    else:
      h5libver = "latest" # default
      
    npn = Network_place_neurons.NetworkPlaceNeurons(config_file=configFile,
                                                    logFile=self.logFile,
                                                    verbose=True,
                                                    dView=self.dView,
                                                    h5libver=h5libver)

    npn.writeDataHDF5(positionFile)

    self.stopParallel()
    self.closeLogFile()

    
  ############################################################################
    
  def touchDetection(self,args):
    # self.networkPath = args.path
    print("Touch detection")
    print("Network path: " + str(self.networkPath))

    if(args.hvsize is not None):
      hyperVoxelSize = int(args.hvsize)
    else:
      hyperVoxelSize = 100

    if(args.volumeID is not None):
      volumeID = args.volumeID
    else:
      volumeID = None
      
    configFile = self.networkPath + "/network-config.json"
    positionFile = self.networkPath + "/network-neuron-positions.hdf5"
    logFileName = self.networkPath + "/logFile-touch-detection.txt"
    saveFile = self.networkPath + "/voxels/network-putative-synapses.hdf5"

    voxelDir = self.networkPath + "/voxels"
    if not os.path.exists(voxelDir):
      os.makedirs(voxelDir)

    
    self.setupLogFile(logFileName) # sets self.logFile
    self.setupParallel() # sets self.dView and self.lbView

    if(args.h5legacy):
      h5libver = "earliest"
    else:
      h5libver = "latest" # default
    
    import Network_connect_voxel
    
    if(args.cont):
      # Continue previous run
      print("Continuing previous touch detection")
      
      ncv = Network_connect_voxel.NetworkConnectVoxel(configFile=configFile,
                                                      positionFile=positionFile,
                                                      logFile=self.logFile,
                                                      saveFile=saveFile,
                                                      SlurmID=self.SlurmID,
                                                      volumeID=volumeID,
                                                      rc=self.rc,
                                                      hyperVoxelSize\
                                                        =hyperVoxelSize,
                                                      h5libver=h5libver,
                                                    restartDetectionFlag=False)

      
    else:
      ncv = Network_connect_voxel.NetworkConnectVoxel(configFile=configFile,
                                                      positionFile=positionFile,
                                                      logFile=self.logFile,
                                                      saveFile=saveFile,
                                                      SlurmID=self.SlurmID,
                                                      volumeID=volumeID,
                                                      rc=self.rc,
                                                      h5libver=h5libver,
                                                      hyperVoxelSize\
                                                        =hyperVoxelSize)
    self.stopParallel()
    self.closeLogFile()

  ############################################################################
    
  def pruneSynapses(self,args):
    # self.networkPath = args.path
    print("Prune synapses")
    print("Network path: " + str(self.networkPath))

    import Network_connect_voxel_prune

    logFileName = self.networkPath + "/logFile-synapse-pruning.txt"

    workLog = self.networkPath + "/network-putative-synapses-worklog.hdf5" 
    
    self.setupLogFile(logFileName) # sets self.logFile
    self.setupParallel() # sets self.dView and self.lbView

    # Optionally set this
    scratchPath = None

    if(args.mergeonly):
      preMergeOnly = True
    else:
      preMergeOnly = False

    print("preMergeOnly : " + str(preMergeOnly))

    if(args.h5legacy):
      h5libver = "earliest"
    else:
      h5libver = "latest" # default
    
    ncvp = Network_connect_voxel_prune.NetworkConnectVoxelPrune(
                  workHistoryFile=workLog,
                  logFile=self.logFile,
                  logFileName=logFileName,
                  dView=self.dView, lbView=self.lbView,
                  scratchPath=scratchPath,
                  h5libver=h5libver,
                  preMergeOnly=preMergeOnly)

    
    self.stopParallel()
    self.closeLogFile()
   

  ############################################################################

  def setupInput(self,args):

    from Network_input import NetworkInput
    
    print("Setting up inputs, assuming input.json exists")
    logFileName = self.networkPath + "/logFile-setup-input.log"
    self.setupLogFile(logFileName) # sets self.logFile
    self.setupParallel() # sets self.dView and self.lbView
    
    if input in args:
      inputConfig = args.input
    else:
      inputConfig = self.networkPath + "/input.json"

    if(not os.path.isfile(inputConfig)):
      print("Missing input config file: " + str(inputConfig))
      return
      
    networkFile = self.networkPath \
                  + "/network-connect-voxel-pruned-synapse-file.hdf5"

    spikeFile = self.networkPath + "/input-spikes.hdf5"
    
    ni = NetworkInput(inputConfigFile=inputConfig,
                      HDF5networkFile=networkFile,
                      spikeDataFileName=spikeFile)

    self.stopParallel()
    self.closeLogFile()
    
    
    
  ############################################################################

  def exportToSONATA(self,args):

    from ConvertNetwork import ConvertNetwork
    
    print("Exporting to SONATA format")
    print("Network path: " + str(self.networkPath))

    networkFile = self.networkPath \
                  + "/network-connect-voxel-pruned-synapse-file.hdf5"

    inputFile = self.networkPath + "/input-spikes.hdf5"


    outDir = self.networkPath + "/SONATA/"

    cn = ConvertNetwork(networkFile=networkFile,
                        inputFile=inputFile,
                        outDir=outDir)
    
  ############################################################################

  def simulate(self,args):

    networkFile = self.networkPath + "/network-connect-voxel-pruned-synapse-file.hdf5"
    inputFile = self.networkPath + "/input-spikes.hdf5"

    cmdStr = "nrnivmodl cellspecs/mechanisms_with_modulation && mpiexec -n 10 -map-by socket:OVERSUBSCRIBE python3 Network_simulate.py " + networkFile + " " + inputFile
    os.system(cmdStr)
  
  ############################################################################
  
  def analyse(self,args):

    print("Add analysis code here, see Network_analyse.py")
    
  ############################################################################

  def setupParallel(self):
    self.SlurmID = os.getenv('SLURM_JOBID')

    if(self.SlurmID is None):
      self.SlurmID = self.nextRunID()
    else:
      self.SlurmID = int(self.SlurmID)
    
    self.logFile.write("Using SlurmID: " + str(self.SlurmID))

    if(os.getenv('IPYTHON_PROFILE') is not None):

      self.logFile.write('Creating ipyparallel client\n')
      
      from ipyparallel import Client
      #self.rc = Client(profile=os.getenv('IPYTHON_PROFILE'),
      #            # sshserver='127.0.0.1',
      #            debug=False)
      
      ufile = os.getenv('IPYTHONDIR') + "/profile_" \
              + os.getenv('IPYTHON_PROFILE') \
              + "/security/ipcontroller-client.json"
      self.rc = Client(url_file=ufile, timeout=120, debug=False)
      
      self.logFile.write('Client IDs: ' + str(self.rc.ids))

      # http://davidmasad.com/blog/simulation-with-ipyparallel/
      # http://people.duke.edu/~ccc14/sta-663-2016/19C_IPyParallel.html
      self.dView = self.rc.direct_view(targets='all') # rc[:] # Direct view into clients
      self.lbView = self.rc.load_balanced_view(targets='all')

      # Define nc globally
      # self.dView.execute("nc = None",block=True)
    else:
      self.logFile.write("No IPYTHON_PROFILE enviroment variable set, running in serial")
      self.dView = None
      self.lbView = None
      self.rc = None

  ############################################################################

  def stopParallel(self):

    # Disable this function, keep the pool running for now
    return
  
    if(self.rc is not None):
      print("Stopping ipyparallel")
      self.rc.shutdown(hub=True)

  ############################################################################
      
  def setupLogFile(self, logFileName):
    self.logFile = open(logFileName,'w')
    self.logFile.write('Starting log file\n')

  ############################################################################

  def closeLogFile(self):

    stop = timeit.default_timer()

    print("\nProgram run time: " + str(stop - self.start ))

    self.logFile.write("Program run time: " + str(stop - self.start))
    self.logFile.write("End of log. Closing file.")
    self.logFile.close()   
    
##############################################################################


  def nextRunID(self):

    import pickle
    
    runIDfile = ".runID.pickle"

    try:
      if(os.path.isfile(runIDfile)):
      
        with open(runIDfile,'rb') as f:
          runID = pickle.load(f)
          nextID = int(np.ceil(np.max(runID)) + 1)

        runID.append(nextID)
        
        with open(runIDfile,'wb') as f:
          pickle.dump(runID,f,-1)

      else:
      
        with open(runIDfile,'wb') as f:
          nextID = 1
          runID = [1]
          pickle.dump(runID,f,-1)
        
    except Exception as e:
      import traceback
      tstr = traceback.format_exc()
      print(tstr)

      print("Problem reading .runID.pickle file, setting runID to 0")
      import pdb
      pdb.set_trace()
      return 0

    print("Using runID = " + str(nextID))
  
    return nextID


  



##############################################################################


if __name__ == "__main__":

  import argparse
  parser = argparse.ArgumentParser(description="Microcircuit generation")
  parser.add_argument("action", choices=["init","place","detect",
                                         "prune","input","export","analyse","convert","simulate","help"],
                      help="Action to do")
  parser.add_argument("path", help="Storage path for network files")
  parser.add_argument("--size",type=int,help="Number of neurons",
                      default=None)
  parser.add_argument("-cont", "--cont",help="Continue partial touch detection",
                      action="store_true")
  parser.add_argument("-hvsize", "--hvsize",help="Hyper voxel size, 100 good value for full striatum, for small runs, use smaller values to more evenly distribute the workload between workers")
  parser.add_argument("--volumeID", help="Specify volumeID for detection step")
  parser.add_argument("--mergeonly","--onlymerge", help="Only merge synapses in hyper voxels into a big file. Pre-processing to pruning, normally run before. This allows the user to run this separately.",action="store_true")
  parser.add_argument("--h5legacy",help="Use legacy hdf5 support",action="store_true")
  parser.add_argument("--profile",help="Run python cProfile",action="store_true")
  parser.add_argument("--nchannels",type=int,help="Number of functional channels in the structure, affects connectivity and input correlation",default=1)
  parser.add_argument("--input",help="Input json config file")
  
  args = parser.parse_args()
  
  if(args.path is not None):
    if(args.path[-1] == "/"):
      args.path = args.path[:-1]

  snudda = Snudda(args.path)
  
  actions = { "init" : snudda.initConfig,
              "place" : snudda.placeNeurons,
              "detect" : snudda.touchDetection,
              "prune" : snudda.pruneSynapses,
              "input" : snudda.setupInput,
              "export" : snudda.exportToSONATA,
              "convert" : snudda.exportToSONATA,
              "analyse" : snudda.analyse,
              "simulate" : snudda.simulate,
              "help" : snudda.helpInfo}

  
  
  if(args.profile):
    profFile = "profile-"+args.action+".prof"
    print("Saving profile data to: " + profFile)
    import cProfile
    cProfile.run("actions[args.action](args)", profFile)

    # To analyse profile data:
    import pstats
    from pstats import SortKey
    p = pstats.Stats(profFile)
    p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats(30)
    
  else:
    # Performing the requested action
    actions[args.action](args)
