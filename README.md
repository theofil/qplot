<h1> Quick plotting macros with Python and ROOT </h1>

### Some example commands:
```
python -i ~/qplot/qplot.py ../var3/perfNano_SingleNeutrino_PU200.root ../var1/perfNano_SingleNeutrino_PU200.root ../def/perfNano_SingleNeutrino_PU200.root ../var2/perfNano_SingleNeutrino_PU200.root -var L1PuppiMet_pt -bins "10,0,200" --setlogy --leg "#DeltaP_{T} = 5 GeV,#DeltaP_{T} = 1 GeV,#DeltaP_{T} = 0.25 GeV,#DeltaP_{T} = 0.10 GeV " -o singleNu


python -i ~/qplot/qplot.py ../var3/perfNano_SingleNeutrino_PU200.root ../var1/perfNano_SingleNeutrino_PU200.root ../def/perfNano_SingleNeutrino_PU200.root ../var2/perfNano_SingleNeutrino_PU200.root -var L1PFJets_pt -bins "100,0,10000" --setlogy --leg "#DeltaP_{T} = 5 GeV,#DeltaP_{T} = 1 GeV,#DeltaP_{T} = 0.25 GeV,#DeltaP_{T} = 0.10 GeV " -o singleNu

python -i ~/qplot/qplot.py ../var3/perfNano_SingleNeutrino_PU200.root ../var1/perfNano_SingleNeutrino_PU200.root ../def/perfNano_SingleNeutrino_PU200.root ../var2/perfNano_SingleNeutrino_PU200.root -var "L1PFJets_pt[4]" -bins "100,0,10000" --setlogy --leg "#DeltaP_{T} = 5 GeV,#DeltaP_{T} = 1 GeV,#DeltaP_{T} = 0.25 GeV,#DeltaP_{T} = 0.10 GeV " -o singleNu -gf 0.3
```



