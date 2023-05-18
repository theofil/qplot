from __future__ import print_function
import os, re, sys
from array import array
import itertools


import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(False)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

### parse external parameters
import argparse

### overide default argparse behavior of the error method 
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

parser = MyParser()
parser = argparse.ArgumentParser(description='making friends')
parser.add_argument('files', nargs='+', help='needs at minimum 1 file')
parser.add_argument('--output', default = '', help = 'name of the plot directory to be created')
parser.add_argument('--ttree', default = '', help = 'name of the tree, if is inside a TDir, Dirname/TreeName, otherwise will attemp to fetch from ListOfKnownTTrees')
parser.add_argument('--xs', default = 1.0, help = 'user provided cross section for normalization', type=float)
parser.add_argument('--genWeight', default = "genWeight", help = 'MC weight from event generator', type=str)
parser.add_argument('--goFast', default = 1.0, help = 'if set, will only process fraction of the entries', type=float)
args = parser.parse_args()

# https://root.cern.ch/root/html534/guides/users-guide/InputOutput.html#the-logical-root-file-tfile-and-tkey
def printListOfkeys(tfile):tfile.GetListOfKeys().Print()

### print list of possible variables of the ROOT file
def printListOfLeaves(myttree, filename = ''):
    if filename != '': 
	fp = open(filename, 'w')
        print('opening %s to write the list of leaves for %s'%(filename, myttree.GetName()))
        for leave in myttree.GetListOfLeaves(): 
            print(leave)
            fp.write(str(leave)+'\n')
        print('closing %s'%filename)
        fp.close()
    else:
    	for leave in myttree.GetListOfLeaves(): 
            print(leave)

# make a simple counter
class counter:
    """counting events"""
    pass

### list of known TTrees
listOfknownTrees = ['Events','events', 'ntuple/tree','tree']

if __name__ == "__main__":
    tfiles = [ROOT.TFile.Open(f) for f in args.files]

    ### read the TTrees from files check if ttree is from list of known, or force to use external
    if args.ttree!='':listOfknownTrees = [args.ttree]

    ttrees = [tfile.Get(ttree) for tfile in tfiles  for ttree in listOfknownTrees if tfile != None and tfile.Get(ttree)!=None]
    for ttree in ttrees: ttree.tfile = ttree.GetCurrentFile()

    if len(ttrees) != len(tfiles): 
	print('not all tfiles have been found with a valid ttree, exiting')
	os._exit(0)

    minimalPrint = True


    ### check if all ttrees have the same name and set it to equal to args.ttree, print warning if not
    ttreeNames = [ttree.GetName() for ttree in ttrees]
    if len(set(ttreeNames))!=1 and len(ttreeNames)>0: print('Warning: not all TTrees have the same name %s'%ttreeNames)
    else: args.ttree = ttreeNames[0]


    ### RDataFrame of all files
    print("Getting sum of weights for all input files")
    sumWtot = 0
    Ntot = 0
    for ii, ttree in enumerate(ttrees):
	df = ROOT.RDataFrame(ttree)
        sumW = 0
        try:
	    sumW = df.Sum(args.genWeight).GetValue() 
	except TypeError:
	    print(args.genWeight, " is not part of the given ttrees, use --genWeight branchName to fix this or assume no such branch and count each entry as 1 event")
            sumW = ttree.GetEntries()
        print('%s with %d entries and sumW = %2.1f'%(tfiles[ii].GetName(), ttree.GetEntries(), sumW))
        Ntot += ttree.GetEntries()
        sumWtot += sumW
    
    print("sumWtot %d   Ntot %d"%(sumWtot, Ntot))

    ### one output tree for all inputs, using the name of the first by default 
    outname = tfiles[0].GetName()[0:-4].split('/')[-1]+'friend'+'.root' 

    ### change the outname on user's request
    if args.output != '': outname = args.output 
    ofile = ROOT.TFile(outname,"RECREATE")
    otree = ROOT.TTree(ttree.GetName(), ttree.GetName()) # same name as original

    hSumW  = ROOT.TH1D("hSumW","hSumW",1, 0, 1)
    hSumW.Sumw2()

    ### ttree variables
    tvars = []
   
    t_kWeight      = array('f', [0]); tvars += [t_kWeight]
    t_kFile        = array('i', [0]); tvars += [t_kFile]

    t_GenLLM       = array('f', [0]); tvars += [t_GenLLM]
    t_GenLLY       = array('f', [0]); tvars += [t_GenLLY]
    t_GenLLPt      = array('f', [0]); tvars += [t_GenLLPt]
    t_GenLLId      = array('f', [0]); tvars += [t_GenLLId]

    nGenJetMax = 15
    t_nGenJet      = array('i', [0]); tvars += [t_nGenJet]
    t_GenJet_pt    = array('f', [-99.9 for i in range(nGenJetMax)]); tvars += [t_GenJet_pt]
    t_GenJet_eta   = array('f', [-99.9 for i in range(nGenJetMax)]); tvars += [t_GenJet_eta]

    nGenLeptonMax = 4
    t_nGenLepton      = array('i', [0]); tvars += [t_nGenLepton]
    t_GenLepton_pt    = array('f', [-99.9 for i in range(nGenLeptonMax)]); tvars += [t_GenLepton_pt]
    t_GenLepton_eta   = array('f', [-99.9 for i in range(nGenLeptonMax)]); tvars += [t_GenLepton_eta]
    t_GenLepton_pdgId = array('i', [-99 for i in range(nGenLeptonMax)]); tvars += [t_GenLepton_pdgId]

    otree.Branch("kWeight",     t_kWeight,      "kWeight/F") 
    otree.Branch("kFile",       t_kFile,        "kFile/I") 
    otree.Branch("GenLLM",      t_GenLLM,       "GenLLM/F") 
    otree.Branch("GenLLY",      t_GenLLY,       "GenLLY/F") 
    otree.Branch("GenLLPt",     t_GenLLPt,      "GenLLPt/F") 
    otree.Branch("GenLLId",     t_GenLLId,      "GenLLId/F") 

    otree.Branch("nGenJet",     t_nGenJet,      "nGenJet/I") 
    otree.Branch("GenJet_pt",   t_GenJet_pt,    "GenJet_pt[nGenJet]/F") 
    otree.Branch("GenJet_eta",  t_GenJet_eta,   "GenJet_eta[nGenJet]/F") 

    otree.Branch("nGenLepton",     t_nGenLepton,      "nGenLepton/I") 
    otree.Branch("GenLepton_pt",   t_GenLepton_pt,    "GenLepton_pt[nGenLepton]/F") 
    otree.Branch("GenLepton_eta",  t_GenLepton_eta,   "GenLepton_eta[nGenLepton]/F") 
    otree.Branch("GenLepton_pdgId",  t_GenLepton_pdgId,   "GenLepton_pdgId[nGenLepton]/I") 

   
    def reset():
	global tvars
	for var in tvars:
	    typecode = var.typecode
	    for i in range(len(var)):
		if typecode == 'f': var[i] = -99.9
		if typecode == 'i': var[i] = int(-99)
		if typecode == 'B': var[i] = False

    count = counter()
    count.alleve   = 0
    count.sumW     = 0
    count.sumW2    = 0

    ### loop over the trees
    for ii,ttree in enumerate(ttrees):
	print("opening %s"%tfiles[ii].GetName())

	### start the bloody event loop for each tree
	for iev, event in enumerate(ttree):
	    if args.goFast and iev >=  args.goFast*ttree.GetEntries()  : break
	    if minimalPrint and iev%10000 == 0: print('event %d of %s'%(iev, tfiles[ii].GetName()))

            ### magic starts here
	    reset()

	    nGenDressedLepton = event.nGenDressedLepton
            t_kWeight[0]      = event.genWeight*args.xs/sumWtot 
            t_kFile[0]        = ii 
            count.sumW        += t_kWeight[0]
            count.sumW2       += t_kWeight[0]*t_kWeight[0]
            hSumW.Fill(0, t_kWeight[0])

            GenLeptons = []
            for i in range(event.nGenDressedLepton):
		GenLepton_pt         = event.GenDressedLepton_pt[i]
		GenLepton_eta        = event.GenDressedLepton_eta[i]
		GenLepton_phi        = event.GenDressedLepton_phi[i]
		GenLepton_mass       = event.GenDressedLepton_mass[i]
		GenLepton_pdgId      = event.GenDressedLepton_pdgId[i]
		GenLepton            = ROOT.TLorentzVector()
		GenLepton.SetPtEtaPhiM(GenLepton_pt, GenLepton_eta, GenLepton_phi, GenLepton_mass)
                GenLepton.pdgId      = GenLepton_pdgId
		GenLeptons += [GenLepton]
                
	    if len(GenLeptons) >= 2:
		genl1 = GenLeptons[0]
		genl2 = GenLeptons[1]
		t_GenLLM[0]  = (genl1 + genl2).M()        
		t_GenLLY[0]  = (genl1 + genl2).Y()        
		t_GenLLPt[0] = (genl1 + genl2).Pt()        
		t_GenLLId[0] = genl1.pdgId*genl2.pdgId       




            GenJets = []
            for i in range(event.nGenJet):
		GenJetpt         = event.GenJet_pt[i]
		GenJeteta        = event.GenJet_eta[i]
		GenJetphi        = event.GenJet_phi[i]
		GenJetmass       = event.GenJet_mass[i]
		GenJet           = ROOT.TLorentzVector()
		GenJet.SetPtEtaPhiM(GenJetpt, GenJeteta, GenJetphi, GenJetmass)
                if GenJet.Pt()>20:
		    GenJets += [GenJet]

            nJetsRemoved = 0
	    for lepton in GenLeptons:
		for GenJet in GenJets:
		    DR = GenJet.DeltaR(lepton)
		    if DR < 0.4:
			GenJets.remove(GenJet)
			nJetsRemoved += 1

	    t_nGenJet[0]  = len(GenJets)
            nGenJetToStore = min(nGenJetMax, t_nGenJet[0])
	    for i in range(nGenJetToStore):
		t_GenJet_pt[i] = round(GenJets[i].Pt(), 1)
		t_GenJet_eta[i] = round(GenJets[i].Eta(), 2)

	    t_nGenLepton[0]  = len(GenLeptons)
            nGenLeptonToStore = min(nGenLeptonMax, t_nGenLepton[0])
	    for i in range(nGenLeptonToStore):
		t_GenLepton_pt[i] = round(GenLeptons[i].Pt(), 1)
		t_GenLepton_eta[i] = round(GenLeptons[i].Eta(), 2)
		t_GenLepton_pdgId[i] = GenLeptons[i].pdgId


            ### fill tree
	    otree.Fill()
	    count.alleve += 1

    print('hSumW.Integral() %2.1f'%hSumW.Integral())
    print('number of events processed %d'%count.alleve)
    print('number of entries in the TTree %d'%ttree.GetEntries())
    print('number of sumW %3.1f'%count.sumW)
    print('number of sumW2 %3.1f'%count.sumW2)

    ### creating output 
    ofile.cd()
    otree.Write()
    hSumW.Write()
    ofile.Write()
    ofile.Close()
   
     
