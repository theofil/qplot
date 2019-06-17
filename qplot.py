from __future__ import print_function
import os, re
from array import array
import itertools
#from optparse import OptionParser

import ROOT 
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(False)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

import argparse
parser = argparse.ArgumentParser(description='overlay ROOT histograms from different files')
parser.add_argument('files', nargs='+', help='needs at minimum 1 file')
#parser.add_argument('files', nargs='?', help='needs at minimum 1 file')
parser.add_argument('-o','--output', default = 'plot_dir', help = 'name of the plot directory to be created')
parser.add_argument('-tree','--tree', default = 'Events', help = 'name of the tree, if is inside a TDirectory exampleDir, should be exampleDir/TreeName')
parser.add_argument('-var','--var', nargs='?', help = 'name of the branch, to be printed', default = 'noVars')
parser.add_argument('-gf','--goFast', default = 1.0, type=float, help = 'process a fraction of  the events for each tree')
parser.add_argument('-bins','--bins', default = '100,0,100', help = 'bins is a string that holds nBins, xMin, xMax')
parser.add_argument('-ax','-axesTitles','--axesTitles', help = 'x-axisTitle, yaxisTitle')
parser.add_argument('-sel','--sel', default='', help = 'TCut selection')
parser.add_argument('-leg','--leg', default='', help = 'list of name for the TLegend')
parser.add_argument('-setlogy','--setlogy', help = 'set log scale in the y-axis', action='store_true')
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

### 
if len(args.files) == 0: 
    sys.exit('this script needs at least 1 valid ROOT file')    

### open the ROOT files
tfiles = [ROOT.TFile.Open(f) for f in args.files]
ttrees = [tfile.Get(args.tree) for tfile in tfiles]

plotsReady = False

if args.var == 'noVars':
    print('no variables to process were given, leaving you to play in interactive shell') 
    for ii, tfile in enumerate(tfiles):
        print("Opened tfiles[%d] = %s with ttree[%d] = %s"%(ii, tfile.GetName(), ii, ttrees[ii].GetName()))

### make histograms of the same 1 variable stored in identacally structured ttrees, stored in different files
if isinstance(args.var, list):
    binning = args.bins.split(',')
    nBins, xMin, xMax = int(binning[0]), float(binning[1]), float(binning[2])
    if not args.axesTitles: args.axesTitles = '%s,Events'%(str(args.var[0]))
    histos = [ROOT.TH1F(str(id(ttree))+str(args.var[0]), str(args.axesTitles), nBins, xMin, xMax) for ttree in ttrees]
    colors = [1, 2, 4, 6, 7, 8, 9]
    styles = [1, 2, 3, 4, 5, 6, 7]
    for ii, histo in enumerate(histos): 
        histo.Sumw2()
        histo.SetTitle(args.leg.split(',')[ii])
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
        ttrees[ii].Draw(str(args.var[0])+'>>'+histos[ii].GetName(), str(args.sel), "goff", maxEntries)
    plotsReady = True

### plot histograms
if plotsReady:
    c1 = ROOT.TCanvas()
    c1.cd()
    if args.setlogy: c1.SetLogy()
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
    filePDF = args.output+'/'+args.var[0]+'_'+filename+'.pdf' 
    filePNG = args.output+'/'+args.var[0]+'_'+filename+'.png'
    print("saving: \n"+filePDF+"\n"+filePNG)
    c1.SaveAs(filePDF)   
    c1.SaveAs(filePNG)   


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

    
def setAlias(myttree, aliases): 
     for x, y in aliases.items():
         print('seting alias %s : %s'%(x, y))
         myttree.SetAlias(x, y)

# https://root.cern.ch/root/html534/guides/users-guide/InputOutput.html#the-logical-root-file-tfile-and-tkey
def printListOfkeys(tfile):tfile.GetListOfKeys().Print()

#paveText = rt.TPaveText(px1, py1, px2, py2,"NDC")
#paveText.SetBorderSize(0)
#paveText.SetFillColor(0)
#paveText.SetFillStyle(0)
#paveText.SetTextSize(26)
#paveText.SetTextFont(43)
#paveText.SetTextColor(rt.kBlue)
#paveText.AddText(paveTitle)
#paveText.Draw("same")
