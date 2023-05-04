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

### overide default argparse behavior of the error method 
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

parser = MyParser()

parser.add_argument('files', nargs='+', help='needs at minimum 1 file')
parser.add_argument('--ttree', default = '', help = 'name of the tree, if is inside a TDir, Dirname/TreeName, otherwise will attemp to fetch from ListOfKnownTTrees')
parser.add_argument('--var', nargs='?', help = 'name of the branch, to be printed', default = '')
parser.add_argument('--goFast', default = 1.0, type=float, help = 'process a fraction of  the events for each tree')
parser.add_argument('--bins', default = '', type = string2list, help = 'bins is a string that holds nBins, xMin, xMax')
parser.add_argument('--xtitle', default = '', help = 'x-axis title')
parser.add_argument('--yrange', default = '', help = 'y-axis range')
parser.add_argument('--ytitle', default = '', help = 'y-axis title')
parser.add_argument('--sel', default='', help = 'TCut selection')
parser.add_argument('--drawopt', default = '', help = 'draw options')
parser.add_argument('--leg', default='', type =string2list, help = 'list of name for the TLegend')
parser.add_argument('--logy', help = 'set log scale in the y-axis', action='store_true')
parser.add_argument('--norm', help = 'normalize histograms', action='store_true')
parser.add_argument('--logx', help = 'set log scale in the x-axis', action='store_true')
parser.add_argument('--nover', help = 'don\'t move overflow to last bin, by default is True',     action='store_false')
parser.add_argument('--nunder', help = 'don\'t move underflow to first bin, by default is True',  action='store_false')
parser.add_argument('--debug', help = 'debug mode, verbose print-out',  action='store_true')
parser.add_argument('--legpos', default = '0.65,0.75,0.93,0.90', help = 'positioning of the legend, default is top-right: 0.65, 0.75 , 0.93, 0.90')
parser.add_argument('--save', nargs='?', default = '', help = 'give filename of the figures to be saved, will produce filename.pdf and filename.png')
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

### list of known TTrees
listOfknownTrees = ['Events','events', 'ntuple/tree','tree']

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

### in case there is any question
yes = {'yes','y' }
no = {'no','n',''}

### save a figure
def save(filename):
    outputDir = 'qplots'
    print('creating folder',outputDir,' if does not already exist and saving figures')
    os.system("mkdir -p "+outputDir)
    if not os.path.exists(outputDir+'/index.php'):
        pathname = os.path.dirname(sys.argv[0])        
        os.system("cp "+pathname+"/index.php "+outputDir)
    filePDF = outputDir+'/'+filename+'.pdf' 
    filePNG = outputDir+'/'+filename+'.png'
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

# have fun with uproot
def fun():
    import uproot
    from matplotlib import pyplot as plt 
    #return [uproot.open(ttree.tfile.GetName())[ttree.GetName()] for ttree in ttrees] 
    return [uproot.open(tfile.GetName())[ttree] for tfile in tfiles  for ttree in listOfknownTrees if tfile != None and tfile.Get(ttree)!=None]

def makeHistos(histos):
    # convert strings to lists if needed
    if isinstance(args.leg,  str): args.leg = [arg for arg in args.leg.split(',')]
    if isinstance(args.bins, str): args.bins = [arg for arg in args.bins.split(',')]
    if isinstance(args.var,  str): args.var = [arg for arg in args.var.split(',')]
    if isinstance(args.sel,  str): args.sel = [arg for arg in args.sel.split(',')]
    # if histograms already exist, erase them 
    while(len(histos)!=0):
         print('deleting %s'%(histos[-1]))
         histos[-1].Delete()
         histos.pop()

    plotElements = ((x,y,z) for x in ttrees for y in args.var for z in args.sel)

    for ii, plotElement in enumerate(plotElements):
        # unpack plotElement
        (ttree, var, sel) = plotElement
        maxEntries = ttree.GetEntries()
        if args.goFast < 1.0: maxEntries = int(args.goFast*maxEntries)
        ### plot same variable from many different root files
        # if no binning has been defined, use automatic binning from ROOT (1D histos)
        if len(var.split(':')) == 1 and args.bins == [''] and ii==0:
            if(args.debug): print('str(var) = ',str(var))
            ttree.Draw(str(var), str(sel), "goff", maxEntries)
            nBins = ROOT.htemp.GetNbinsX() 
            xMin  = ROOT.htemp.GetXaxis().GetBinLowEdge(1)
            xMax  = ROOT.htemp.GetXaxis().GetBinLowEdge(nBins) + ROOT.htemp.GetXaxis().GetBinWidth(nBins) 
            print('automatic binning from ROOT nBins %d xMin %f xMax %f is set to args.bin'%(nBins, xMin, xMax))
            args.bins = [nBins, xMin, xMax]
            print('setting args.xtitle: %s'%args.xtitle)
            print('setting args.ytitle: %s'%args.ytitle)

        # creating 1D histograms
        if len(var.split(':')) == 1 and len(args.bins) == 3:
            nBins = int(args.bins[0])
            xMin  = float(args.bins[1])
            xMax  = float(args.bins[2])
            histoID = str(id(ttree.tfile)+id(ttree))+str(var)+str(sel)       
            histoID = histoID.replace('/','__')
            histoID = histoID.replace('(','_')
            histoID = histoID.replace(')','_')
            histoID = histoID.replace('*','')
            histo  = ROOT.TH1F(histoID, ';%s;%s'%(args.xtitle, args.ytitle), nBins, xMin, xMax) 
            histo.Sumw2()
            histoTitle = ttree.tfile.GetName()+ttree.GetName()+'_'+var+'_'+sel
            histoTitle = histoTitle.replace('/','__')
            histo.SetTitle(histoTitle)
            #print('creating histo for %s %s %s %s %s and maxEntries %d out of %d '%(ttree.tfile.GetName(), ttree.GetName(), var, sel, histoID, maxEntries, ttree.GetEntries()))
            drawCmd = str(var)+'>>'+histo.GetName()
            if(args.debug): print('histo[%d] with Draw(%s, %s, "goff", %d) in %s of %s'%(ii, drawCmd, str(sel), maxEntries, ttree.GetName(), ttree.tfile.GetName()))
            ttree.Draw(drawCmd, str(sel), "goff", maxEntries)
            histos += [histo]

    ### print sum of weights 
    for ii, histo in enumerate(histos):
	    if len(args.leg) == len(histos) and args.leg!='':histo.SetTitle(str(args.leg[ii]))
	    sumW  = histo.GetSumOfWeights()
	    print('%s has sumW = %2.1f'%(histo.GetTitle(), sumW))
         
    if args.nover: moveOverflow(histos)
    if args.nunder: moveUnderflow(histos)

    plotHistos(histos)


def plotHistos(histos):
    # convert strings to lists if needed
    if isinstance(args.leg,  str): args.leg = [arg for arg in args.leg.split(',')]
    if isinstance(args.bins, str): args.bins = [arg for arg in args.bins.split(',')]
    if isinstance(args.var,  str): args.var = [arg for arg in args.var.split(',')]
    if isinstance(args.sel,  str): args.sel = [arg for arg in args.sel.split(',')]
    # clear legend and canvas
    leg.Clear()
    can1.Clear()
    can1.cd()
    if args.logy: can1.SetLogy()
    if args.logx: can1.SetLogx()
    (lx1, ly1, lx2, ly2) = (float(x) for x in args.legpos.split(','))
    leg.SetX1NDC(lx1)
    leg.SetX2NDC(lx2)
    leg.SetY1NDC(ly1)
    leg.SetY2NDC(ly2)

    # normalize histograms 
    if args.norm: 
        for h in histos: h.Scale(1/h.Integral())


    # find yMin yMax
    yMin = min(h.GetBinContent(h.GetMinimumBin()) for h in histos)
    yMax = 1.1*max(h.GetBinContent(h.GetMaximumBin()) for h in histos)
    
    if args.logy and yMin <= 0: 
        if args.norm: yMin=0.0001 
        else: yMin = 0.5
    if args.logy: yMax=1.5*yMax
    if args.logy and yMax == 0: yMax=1

    if args.yrange !='':
        global ymin, ymax
        yMin = float(args.yrange.split(',')[0])
        yMax = float(args.yrange.split(',')[1])

    print('yMin = %2.3f yMax = %2.3f'%(yMin, yMax))

    for ii,histo in enumerate(histos):
        if len(args.leg) == len(histos) and args.leg!='':histo.SetTitle(str(args.leg[ii]))
        histo.GetXaxis().SetNdivisions(505)
        histo.GetYaxis().SetNdivisions(505)
       
        
        histo.SetLineWidth(4)
        global colors
        global styles
        if(ii >= len(colors)):
            colors += [i for i in range(colors[-1]+1, colors[-1]+ii+1)]
            styles += [i for i in range(styles[-1]+1, styles[-1]+ii+1)]
        histo.SetLineColor(colors[ii])
        histo.SetLineStyle(styles[ii])
        if styles[ii] == 1: histo.SetLineWidth(3)
        if ii==0: 
            drawopt ='hist'
            if args.drawopt != '': drawopt = args.drawopt
            histos[ii].Draw(drawopt)
            histos[ii].GetYaxis().SetRangeUser(yMin, yMax)
        else:
            histos[ii].Draw("hist same")    
    leg.SetTextSize(26)
    leg.SetTextFont(43)
    leg.SetFillColor(ROOT.kWhite)
    leg.SetFillStyle(0)
    leg.SetBorderSize(0)
    for histo in histos:leg.AddEntry(histo, histo.GetTitle(), 'l')
    leg.Draw("same")
    can1.Update()

def guessMissingArgs(args):
    if args.xtitle == '': args.xtitle = args.var
    if args.ytitle == '': 
        if args.norm: args.ytitle = 'Frequency' 
        else: args.ytitle = 'Events / bin'


if __name__ == "__main__":
   print('qplot script by KT, don\'t forget to run it with -i for entering interactive mode, e.g.,: python -i ~/qplot.py file.root')
   tfiles = [ROOT.TFile.Open(f) for f in args.files]

   ### read the TTrees from files check if ttree is from list of known, or force to use external
   if args.ttree!='':listOfknownTrees = [args.ttree]

   ttrees = [tfile.Get(ttree) for tfile in tfiles  for ttree in listOfknownTrees if tfile != None and tfile.Get(ttree)!=None]

   ### add as attribute the tfile name of each tree
   for ttree in ttrees: ttree.tfile = ttree.GetCurrentFile()

   if len(ttrees) != len(tfiles): 
       print('not all tfiles have been found with a valid ttree, exiting')
       os._exit(0)

   ### root data frames
   rdfs = [ROOT.RDataFrame(ttree) for ttree in ttrees]
   weightBranchName = "kWeight"
   sumWs = []
   for ii, rdf in enumerate(rdfs):
       if weightBranchName in rdf.GetColumnNames():
           sumW = rdf.Sum("kWeight").GetValue()
           print('File %s opened with sumW = %2.1f'%(ttrees[ii].tfile.GetName(), sumW))	 
     

   ### check if all ttrees have the same name and set it to equal to args.var, print warning if not
   ttreeNames = [ttree.GetName() for ttree in ttrees]
   if len(set(ttreeNames))!=1 and len(ttreeNames)>0: print('Warning: not all TTrees have the same name %s'%ttreeNames)
   else: args.ttree = ttreeNames[0]
  
   ### create global pointers to TCanvas and TLegend, histos and define color styles and more
   histos = []
   can1 = ROOT.TCanvas('can1','can1')
   (lx1, ly1, lx2, ly2) = (float(x) for x in args.legpos.split(','))
   leg = ROOT.TLegend(lx1, ly1, lx2, ly2)
   colors = [1, 2, 4, 6, 7, 8, 9]
   styles = [1, 2, 3, 4, 5, 6, 7]
   
   ### check if any argument has been given for ploting, print help if not
   if args.var == '': print ('no variable to be used has been given, use printListOfLeaves(ttrees[N]) to browse the different options and set it via args.var = \'myVar\'')
   else: 
       guessMissingArgs(args) 
       makeHistos(histos)
       ### saving output to default folder, qplots
       if args.save==None:save(args.var[0])
       if args.save!=None and args.save!='':save(args.save)
    
       



#paveText = rt.TPaveText(px1, py1, px2, py2,"NDC")
#paveText.SetBorderSize(0)
#paveText.SetFillColor(0)
#paveText.SetFillStyle(0)
#paveText.SetTextSize(26)
#paveText.SetTextFont(43)
#paveText.SetTextColor(rt.kBlue)
#paveText.AddText(paveTitle)
#paveText.Draw("same")
