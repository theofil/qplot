from __future__ import print_function
import os, re, sys
from array import array
import itertools

import ROOT 
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(False)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

### converts parsed parameters from string to list
def string2list(s): 
    try: 
        if isinstance(s, str): s = [x for x in s.split(',')]
        if isinstance(s, tuple): s = [x for x in s]
        return s 
    except: raise argparse.ArgumentTypeError("string must be formatted as 'a, b, c,'")

### parse external parameters
import argparse
parser = argparse.ArgumentParser(description='overlay ROOT histograms from different files')
parser.add_argument('files', nargs='+', help='needs at minimum 1 file')
parser.add_argument('--output', default = 'lazySkimmed', help = 'name of the plot directory to be created')
parser.add_argument('--ttree', default = '', help = 'name of the tree, if is inside a TDir, Dirname/TreeName, otherwise will attemp to fetch from ListOfKnownTTrees')
parser.add_argument('--var', nargs='?', help = 'name of the branch, to be printed', default = '')
parser.add_argument('--sel', default='', help = 'TCut selection')
parser.add_argument('--varfile', default = '', help = 'name of the txt file with the variables')
args = parser.parse_args()

# https://root.cern.ch/root/html534/guides/users-guide/InputOutput.html#the-logical-root-file-tfile-and-tkey
def printListOfkeys(tfile):tfile.GetListOfKeys().Print()

### list of known TTrees
listOfknownTrees = ['Events','events', 'ntuple/tree','tree']

if __name__ == "__main__":
   print('lazyskim script by KT, examples:')
   print('    python -i skimming/lazyskim.py sum_EWKWJets.root  --var \'nGenJet,GenJet_pt\'')
   print('    python -i skimming/lazyskim.py sum_EWKWJets.root --varfile vars.txt')
   tfiles = [ROOT.TFile.Open(f) for f in args.files]

   ### read the TTrees from files check if ttree is from list of known, or force to use external
   if args.ttree!='':listOfknownTrees = [args.ttree]

   ttrees = [tfile.Get(ttree) for tfile in tfiles  for ttree in listOfknownTrees if tfile != None and tfile.Get(ttree)!=None]
   for ttree in ttrees: ttree.tfile = ttree.GetCurrentFile()

   if len(ttrees) != len(tfiles): 
       print('not all tfiles have been found with a valid ttree, exiting')
       os._exit(0)

   ### check if all ttrees have the same name and set it to equal to args.var, print warning if not
   ttreeNames = [ttree.GetName() for ttree in ttrees]
   if len(set(ttreeNames))!=1 and len(ttreeNames)>0: print('Warning: not all TTrees have the same name %s'%ttreeNames)
   else: args.ttree = ttreeNames[0]

   ### vars
   noVars = True
   if  args.var != '':
       vars = args.var.split(',')
       noVars = False
   else:
       varfile = open(args.varfile, 'r')   
       vars = [line.rstrip('\n') for line in varfile if line[0] != '#']
       noVars = False
  
   vars = [var for var in vars if var != ''] 

   ### setting branches
   if not noVars:
       print('will save the following vars', vars)
       for ii,ttree in enumerate(ttrees):
           ttree.SetBranchStatus('*',0)
           for var in vars:
               ttree.SetBranchStatus(var,1)

           ### creating output 
           #outname = tfiles[ii].GetName()[0:-4]+'lazyskim'+'.root'
           outname = tfiles[ii].GetName()[0:-4].split('/')[-1]+'lazyskim'+'.root'
           newfile = ROOT.TFile(outname,"RECREATE")
           newTTree = ttree.CloneTree()
           newTTree.Print()
           newfile.Write()
           newfile.Close()
   
     
