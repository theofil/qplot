#!/usr/bin/python
import ROOT as rt

# declarations
f1        = "../PFdef/perfNano_TTbar_PU200.root"
f2        = "../PFnoMu/perfNano_TTbar_PU200.root"
paveTitle = "TTbar_PU200"
treeName  = "Events"

s1        = "PFdef"  #short label for filename
s2        = "PFnoMu" #
l1        = "PF def" #legend for f1
l2        = "PFnoMu" #
plotDir   = "/afs/cern.ch/user/t/theofil/www/images/PFnoMu/"
goFast    = False

#var               = "L1PFMet_pt"
#hist_title        = "; PFMET [GeV]; events"
#nbins, xMin, xMax =  60, 0, 300
var               = "L1PuppiJets_pt"
hist_title        = "; L1PuppiJets_pt [GeV]; events"
nbins, xMin, xMax =  80, 0 , 800
sel               = ""

lx1, ly1, lx2, ly2 = 0.65, 0.8 , 0.93, 0.93
px1, py1, px2, py2 = 0.65, 0.66, 0.87, 0.87

# open the file, read the TTree
fp1 = rt.TFile.Open(f1)
t1 = fp1.Get(treeName)
fp2 = rt.TFile.Open(f2)
t2 = fp2.Get(treeName)

# set TDR style
rt.gROOT.LoadMacro("setTDRStyle.C")
from ROOT import setTDRStyle
setTDRStyle()

# make histograms
h1 = rt.TH1F(var+"_h1",hist_title, nbins, xMin, xMax)
h1.Sumw2() 
h2 = rt.TH1F(var+"_h2",hist_title, nbins, xMin, xMax)
h2.Sumw2() 


# fill histograms
maxEntries = 1000
max1 = t1.GetEntries()
max2 = t2.GetEntries()
print "Entries of the two trees: %d, %d"%(t1.GetEntries(), t2.GetEntries())
if goFast: 
    print "going fast with %d entries"%maxEntries
    max1, max2 = maxEntries, maxEntries

t1.Draw(var+">>"+h1.GetName(),sel,"goff", max1)
h1.SetLineWidth(2)
h1.SetLineColor(rt.kBlack)
h1.SetMarkerColor(rt.kBlack)

t2.Draw(var+">>"+h2.GetName(),sel,"goff", max2)
h2.SetLineWidth(2)
h2.SetLineColor(rt.kRed)
h2.SetMarkerColor(rt.kRed)

### plot
rt.gStyle.SetOptTitle(0)
c1 = rt.TCanvas()
c1.cd()
c1.SetLogy()
h1.Draw("hist")
h2.Draw("hist same")

leg = rt.TLegend(lx1, ly1, lx2, ly2)
leg.SetTextSize(26)
leg.SetTextFont(43)
leg.SetFillColor(rt.kWhite)
leg.SetFillStyle(0)
leg.SetBorderSize(0)
leg.AddEntry(h1, l1,"l")
leg.AddEntry(h2, l2,"l")
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

c1.SaveAs(plotDir+paveTitle+s1+"_"+s2+"_"+var+".png")
c1.SaveAs(plotDir+paveTitle+s1+"_"+s2+"_"+var+".pdf")
