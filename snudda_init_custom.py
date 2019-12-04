from snudda_init import SnuddaInit
from collections import OrderedDict
import json
import os

if __name__ == "__main__":
  
  import argparse
  parser = argparse.ArgumentParser(description="Init custom network")
  parser.add_argument("network",type=str,help="Network path")
  args = parser.parse_args()

  
  
  simName = args.network
  #simName = "networks/SynTest-v6" # MSMS tuning
  #simName = "networks/SynTest-v15"  
  
  # connect network? > True/False
  connectNeurons = 1 #False
  
  configName= simName + "/network-config.json"
  cnc = SnuddaInit(structDef={},configName=configName,nChannels=1)
  cnc.defineStriatum(nMSD1=5,nMSD2=5,nFS=5,nLTS=5,nChIN=5,volumeType="cube")  
  #cnc.defineStriatum(nMSD1=120,nMSD2=120,nFS=20,nLTS=0,nChIN=0,volumeType="slice")

  dirName = os.path.dirname(configName)
  
  if not os.path.exists(dirName):
    os.makedirs(dirName)

  cnc.writeJSON(configName)

  if(not connectNeurons):
    print("Removing all target information, and rewriting config file")
    # Reopen the config file, and remove all connectivity settings, to
    # get an unconnected network

    with open(configName,"r") as f:
      conData = json.load(f,object_pairs_hook=OrderedDict)

    for k in conData:
      if(k.lower() in ["volume", "channels"]):
        continue

      # Remove targets
      if(False):
        x = conData[k]
        del x["targets"]
      
    with open(configName,"w") as f:
      print("Writing to file: " + str(configName))
      json.dump(conData,f,indent=2)
      

  print("Now run:\n./snudda.py place " + simName)
  print("./snudda.py detect " + simName)
  print("./snudda.py prune " + simName)
  print("./snudda.py input " + simName + " --input config/input-tinytest-v4.json")
  print("./snudda.py simulate " + simName \
        + " --voltOut " + simName + "/volt-out.csv --time 10.0")
