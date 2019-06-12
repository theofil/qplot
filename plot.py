#!/usr/bin/python
import ROOT as rt

# declarations
rootdir   = "../ROOTs/"
f1        = "perfTuple_GluGluToHHTo4B_PU200.root"
#f1        = "perfTuple_DYToLL_PU200.root"
paveTitle = "HHTo4b"
treeName  = "ntuple/tree"

s1        = "PFdef"  #short label for filename
s2        = "PFnoMu" #
l1        = "PF def" #legend for f1
l2        = "PFnoMu" #
plotDir   = "/afs/cern.ch/user/t/theofil/www/images/PFnoMu/"
goFast    = True
saveFig   = False


# open the file, read the TTree
fp1 = rt.TFile.Open(rootdir+f1)
t1 = fp1.Get(treeName)

# set TDR style
rt.gROOT.LoadMacro("setTDRStyle.C")
from ROOT import setTDRStyle
setTDRStyle()

# make histograms
var               = "GenAcc_pt"
hist_title        = "; genJet P_T [GeV]; events"
nbins, xMin, xMax =  80, 0 , 800
sel               = ""

lx1, ly1, lx2, ly2 = 0.65, 0.8 , 0.93, 0.93
px1, py1, px2, py2 = 0.65, 0.66, 0.87, 0.87

hist_title = "; events ;" 
h1 = rt.TH1F(var+"_h1",hist_title, nbins, xMin, xMax)


# fill histograms
maxEntries = 1000
max1 = t1.GetEntries()
print "Entries of the tree: %d"%(t1.GetEntries())
if goFast: 
    print "going fast with %d entries"%maxEntries
    max1, max2 = maxEntries, maxEntries

t1.Draw(var+">>"+h1.GetName(),sel,"goff", max1)
h1.SetLineWidth(2)
h1.SetLineColor(rt.kBlack)
h1.SetMarkerColor(rt.kBlack)

### plot
rt.gStyle.SetOptTitle(0)
c1 = rt.TCanvas()
c1.cd()
c1.SetLogy()
h1.Draw("hist")

leg = rt.TLegend(lx1, ly1, lx2, ly2)
leg.SetTextSize(26)
leg.SetTextFont(43)
leg.SetFillColor(rt.kWhite)
leg.SetFillStyle(0)
leg.SetBorderSize(0)
leg.AddEntry(h1, l1,"l")
leg.Draw("same")

paveText = rt.TPaveText(px1, py1, px2, py2,"NDC")
paveText.SetBorderSize(0)
paveText.SetFillColor(0)
paveText.SetFillStyle(0)
paveText.SetTextSize(26)
paveText.SetTextFont(43)
paveText.SetTextColor(rt.kBlue)
paveText.AddText(paveTitle)
paveText.Draw("same")

if saveFig:
    c1.SaveAs(plotDir+paveTitle+s1+"_"+s2+"_"+var+".png")
    c1.SaveAs(plotDir+paveTitle+s1+"_"+s2+"_"+var+".pdf")
