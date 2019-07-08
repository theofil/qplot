from __future__ import print_function
import os, re
from array import array
import itertools

import ROOT 
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(False)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

import argparse
parser = argparse.ArgumentParser(description='overlay ROOT histograms from different files')
parser.add_argument('files', nargs='+', help='needs at minimum 1 file')
#parser.add_argument('files', nargs='?', help='needs at minimum 1 file')
parser.add_argument('-o','--output', default = 'plot_dir', help = 'name of the plot directory to be created')
parser.add_argument('--tree', default = '', help = 'name of the tree, if is inside a TDir, Dirname/TreeName, otherwise will attemp to fetch from ListOfKnownTTrees')
#parser.add_argument('--var', nargs='?', help = 'name of the branch, to be printed', default = 'noVars')
parser.add_argument('--var', nargs='?', help = 'name of the branch, to be printed', default = '')
parser.add_argument('--goFast','--gf', default = 1.0, type=float, help = 'process a fraction of  the events for each tree')
parser.add_argument('--bins', default = '', help = 'bins is a string that holds nBins, xMin, xMax')
parser.add_argument('--xtitle', default = '', help = 'x-axis title')
parser.add_argument('--ytitle', default = '', help = 'y-axis title')
parser.add_argument('--sel', default='', help = 'TCut selection')
parser.add_argument('--leg', default='', help = 'list of name for the TLegend')
parser.add_argument('--logy', help = 'set log scale in the y-axis', action='store_true')
parser.add_argument('--logx', help = 'set log scale in the x-axis', action='store_true')
print('printing help always helps ;-)')
parser.print_help()
print('now start parsing args and execute the program')
args = parser.parse_args()

### set TDR style
ROOT.gROOT.LoadMacro("~/qplot/setTDRStyle.C")
from ROOT import setTDRStyle
setTDRStyle()
ROOT.gStyle.SetOptStat(False)
ROOT.gStyle.SetOptTitle(False)
ROOT.gStyle.SetErrorX(0.5)

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

### open the ROOT files
yes = {'yes','y' }
no = {'no','n',''}
print("opening %s"%args.files)
tfiles = [ROOT.TFile.Open(f) for f in args.files]
listOfknownTrees = ['Events','events', 'ntuple/tree']
ttrees = []
for tfile in tfiles:
    if tfile !=None:
        if args.tree == '':
            for checkTTreeExistance in listOfknownTrees: 
                if tfile.Get(checkTTreeExistance) != None:
                    print("found TTree %s in %s appending it in ttrees"%(checkTTreeExistance, tfile.GetName()))
                    tfile.ttree = tfile.Get(checkTTreeExistance)
                    ttrees += [tfile.ttree]            
        else:
            print("attempting to fetch %s from %s"%(args.tree, tfile.GetName()))
            if tfile.Get(args.tree) != None:
                tfile.ttree = tfile.Get(args.tree)
                ttrees += [tfile.ttree]
        if not hasattr(tfile,'ttree'):
            print("didn't find any ttree inside %s matching the listOfKnownTrees, printing out available keys"%tfile.GetName())
            printListOfkeys(tfile)
            pickUpTTree = raw_input('would you like to pickup one ttree from the list of %s ? (y/[n]):'%tfiles[0].GetName()).lower()
            if(pickUpTTree in yes):
                args.tree = raw_input('ttree name:')
                tfile.ttree = tfile.Get(args.tree)
                ttrees += [tfile.ttree]
        if args.var != '':tfile.var = args.var
        if hasattr(tfile,'ttree') and not hasattr(tfile,'var'):
            pickUpVar = raw_input('no variables to process were given, would you like to pickup one ? (y/[n]):').lower() 
            if(pickUpVar in yes): 
                printListOfLeaves(tfile.ttree)
                tfile.var = raw_input('variable to plot:')
            if len(tfiles): useThisVarFromNowOn = raw_input('would you like to use the same variable for all remaining tfiles ? (y/[n]):').lower()
            if useThisVarFromNowOn: args.var = tfile.var
            if args.bins == '': binsFromInput = raw_input('no binning has been given for %s, would you like to give one ? (y/[n]):'%tfile.var).lower()
            if binsFromInput in yes: 
                args.bins = raw_input('please provide comma separated binning nBinsX, xMin, xMax, ... :') 
                tfile.bins = args.bins
            if args.xtitle =='': xtitleFromInput =  raw_input('no x-title would you like to give one ? (y/[n]):').lower() 
            if xtitleFromInput in yes and args.bins != '': 
                args.xtitle = raw_input('please provide x title:')
            else: args.xtitle = args.var.split(':')[0]
            if args.ytitle =='': ytitleFromInput =  raw_input('no y-title would you like to give one ? (y/[n]):').lower() 
            if ytitleFromInput in yes and args.bins != '': 
                args.ytitle = raw_input('please provide y-title:')
                tfiles.ytitle = args.ytitle
            else:  
                if len(args.var.split(':'))==2: args.ytitle = args.var.split(':')[1]
                else:
                    args.ytitle='Events / bin'
                    tfile.ytitle='Events / bin' 
            # 1D histo
            if len(args.var.split(':'))==1 and len(args.bins.split(','))==3:
                print('creating a TH1F from given input')
                nBins = int(tfile.bins.split(',')[0]) 
                xMin  = float(tfile.bins.split(',')[1]) 
                xMax  = float(tfile.bins.split(',')[2]) 
                histo  = ROOT.TH1F(str(id(tfile.ttree))+str(args.var), ';%s;%s'%(args.xtitle, args.ytitle), nBins, xMin, xMax)            
                maxEntries = tfile.ttree.GetEntries()
                if args.goFast < 1.0: 
                    maxEntries = int(args.goFast*maxEntries)
                    print ("going fast with %d entries out of %d"%(maxEntries, ttrees[ii].GetEntries()))
                tfile.ttree.Draw(str(args.var)+'>>'+histo.GetName(), str(args.sel), "goff", maxEntries)


                 

            
                
    
#ttrees = [tfile.Get(args.tree) for tfile in tfiles]

### global variable signaling that some plots are ready
plotsReady = False


if args.var == 'noVars' and args.files is not None and len(tfiles)>0 and hasattr(tfiles[0],'ttree'):
    pickUpVar = raw_input('no variables to process were given, would you like to pickup one from the list of %s ? (y/[n])'%tfiles[0].GetName()).lower() 
    if(pickUpVar in yes): 
        printListOfLeaves(ttrees[0])
        args.var = raw_input('variable to plot:')
    for ii, tfile in enumerate(tfiles):
        print("Opened tfiles[%d] = %s with ttree[%d] = %s"%(ii, tfile.GetName(), ii, ttrees[ii].GetName()))
        
if args.bins =='100,0,100' and args.var!= 'noVars':
    getBins = raw_input('no binning has been given, use the default \'100,0,100\' ? [press enter for default or give binning to be used]')  
    if(getBins!=''): args.bins = getBins


### make histograms of the same 1 variable stored in identacally structured ttrees, stored in different files
if isinstance(args.var, str) and args.var != '':
    binning = args.bins.split(',')
    nBins, xMin, xMax = int(binning[0]), float(binning[1]), float(binning[2])
    if not args.axesTitles: args.axesTitles = '%s,Events'%(str(args.var))
    histos = [ROOT.TH1F(str(id(ttree))+str(args.var), str(args.axesTitles), nBins, xMin, xMax) for ttree in ttrees]
    colors = [1, 2, 4, 6, 7, 8, 9]
    styles = [1, 2, 3, 4, 5, 6, 7]
    for ii, histo in enumerate(histos): 
        histo.Sumw2()
        if args.leg != '':histo.SetTitle(args.leg.split(',')[ii])
        if args.leg == '':histo.SetTitle(tfiles[ii].GetName())
        histo.GetXaxis().SetTitle(args.axesTitles.split(',')[0])
        histo.GetYaxis().SetTitle(args.axesTitles.split(',')[1])
        histo.SetLineWidth(3)
        histo.SetLineColor(colors[ii])
        histo.SetLineStyle(styles[ii])
        if styles[ii] == 1: histo.SetLineWidth(2)
        histo.GetXaxis().SetNdivisions(505)
    for ii, histo in enumerate(histos):
        maxEntries = ttrees[ii].GetEntries()
        if args.goFast < 1.0: 
            maxEntries = int(args.goFast*maxEntries)
            print ("going fast with %d entries out of %d"%(maxEntries, ttrees[ii].GetEntries()))
        ttrees[ii].Draw(str(args.var)+'>>'+histos[ii].GetName(), str(args.sel), "goff", maxEntries)
    plotsReady = True

### plot histograms
if plotsReady:
    can1 = ROOT.TCanvas()
    can1.cd()
    if args.logy: can1.SetLogy()
    if args.logx: can1.SetLogx()
    histos = sorted(histos, key = lambda h : -h.GetBinContent(h.GetMaximumBin()))
    for ii,histo in enumerate(histos):
        if ii==0: 
            histos[ii].Draw("hist")
        else:
            histos[ii].Draw("hist same")    
    
    lx1, ly1, lx2, ly2 = 0.65, 0.8 , 0.93, 0.93
    leg = ROOT.TLegend(lx1, ly1, lx2, ly2)
    leg.SetTextSize(26)
    leg.SetTextFont(43)
    leg.SetFillColor(ROOT.kWhite)
    leg.SetFillStyle(0)
    leg.SetBorderSize(0)
    for histo in histos:leg.AddEntry(histo, histo.GetTitle(), 'l')
    leg.Draw("same")
 

def save(filename=""):
    os.system("mkdir -p "+args.output)
    filePDF = args.output+'/'+args.var+'_'+filename+'.pdf' 
    filePNG = args.output+'/'+args.var+'_'+filename+'.png'
    print("saving: \n"+filePDF+"\n"+filePNG)
    can1.SaveAs(filePDF)   
    can1.SaveAs(filePNG)   


def moveOverflowToLastBin(h1):
    nBinsX = h1.GetNbinsX()
    overflowBin = nBinsX + 1
    lastBin = nBinsX
    
    overflowBinContent = h1.GetBinContent(overflowBin)
    overflowBinError   = h1.GetBinError  (overflowBin) 
    lastBinContent     = h1.GetBinContent(lastBin)
    lastBinError       = h1.GetBinError  (lastBin) 
    
    totBinContent      = overflowBinContent + lastBinContent
    totBinError        = (overflowBinError*overflowBinError + lastBinError*lastBinError)**0.5
    
    h1.SetBinContent(lastBin, totBinContent)
    h1.SetBinError(lastBin, totBinError)
    h1.SetBinContent(overflowBin, 0)
    h1.SetBinError(overflowBin, 0)


def moveUnderflowToLastBin(h1):
    underflowBin = 0 # underflow bin
    firstBin     = 1 # first bin with low-edge xlow INCLUDED
    
    underflowBinContent = h1.GetBinContent(underflowBin)
    underflowBinError   = h1.GetBinError  (underflowBin) 
    firstBinContent     = h1.GetBinContent(firstBin)
    firstBinError       = h1.GetBinError  (firstBin) 
    
    totBinContent      = underflowBinContent + firstBinContent
    totBinError        = (underflowBinError*underflowBinError + firstBinError*firstBinError)**0.5
    
    h1.SetBinContent(firstBin, totBinContent)
    h1.SetBinError(firstBin, totBinError)
    h1.SetBinContent(underflowBin, 0)
    h1.SetBinError(underflowBin, 0)

def moveOverflow(histos):
    """moves overflow for all histos in the list"""
    for hist in histos: 
        print("moving overflow to last bin for %s"%(hist.GetTitle()))
        moveOverflowToLastBin(hist)

def moveUnderflow(histos):
    """moves underflow for all histos in the list"""
    for hist in histos: 
        print("moving underflow to last bin for %s"%(hist.GetTitle()))
        moveUnderflowToLastBin(hist)


    
def setAlias(myttree, aliases): 
     for x, y in aliases.items():
         print('seting alias %s : %s'%(x, y))
         myttree.SetAlias(x, y)


if plotsReady:
    moveOverflow(histos)
    moveUnderflow(histos)
    can1.Update()

# have fun with uproot
def fun():
    import uproot
    from matplotlib import pyplot as plt 
    return [uproot.open(tfile.GetName())[args.tree] for tfile in tfiles] 
        

#paveText = rt.TPaveText(px1, py1, px2, py2,"NDC")
#paveText.SetBorderSize(0)
#paveText.SetFillColor(0)
#paveText.SetFillStyle(0)
#paveText.SetTextSize(26)
#paveText.SetTextFont(43)
#paveText.SetTextColor(rt.kBlue)
#paveText.AddText(paveTitle)
#paveText.Draw("same")
