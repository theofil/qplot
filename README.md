# qplot stands for quick plot
It is meant to be used for quickly browsing many ROOT files and produce histograms with ROOT/matplotlib and analyze the data with numpy arrays. 

## Usage

Open many ROOT files, search for known ttrees prodice pointers to them via the ttrees python list:

```
python -i ~/qplot/qplot.py *.root
```

or e.g., open one ROOT file and plot different branches, all automatic without worrying for anything but giving the correct variable names:

```
python -i ~/qplot/qplot.py input.root --var 'jet1_pt,jet2_pt,jet3_pt'
```

the script will determine range, binning, axis titles, etc for you.

