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
listOfknownTrees = ['Events','events', 'ntuple/tree','tree','Data']

if __name__ == "__main__":
   print('lazyskim script by KT, example:')
   print('    python3 lazyskim.py ~/files/andreas/VBFHToBB.root --var "nJets,jetPt,jetEta')
   print('please omit any space between the vars that should be only comma separated without any space in between')
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

   for ii,ttree in enumerate(ttrees):
       ### creating output using RDataFrame
       df = ROOT.RDataFrame(ttree)
       #df.Filter([](double t) { return t > 0.; }, {"theta"})
       if args.sel: 
          print('applying the filter: %s'%args.sel)
          df = df.Filter(args.sel)
       outname = tfiles[ii].GetName()[0:-4].split('/')[-1]+'lazyskim'+'.root'
       
       ### print information
       if args.var !='': print('creating %s for the TTree %s and the following branches %s'%(outname, ttree.GetName(), args.var))
       else: print('creating %s for the TTree %s for all branches'%(outname, ttree.GetName()))

       ### save the Snapshot
       df.Snapshot(ttree.GetName(), outname, set(args.var.split(',')))
       #df.Snapshot(ttree.GetName(), outname, {'nJets','jetPt'})
