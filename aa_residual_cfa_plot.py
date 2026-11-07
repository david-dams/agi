"""Render residual-CFA figures from saved results without repeating fits."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output/aa-residual-cfa'
HALVES=('2025H1','2025H2','2026H1')
COLORS={'independent':'#555555','coding':'#225ea8','coding_academic':'#d95f0e'}


def read(path):return list(csv.DictReader(path.open()))


def main():
    points=read(OUT/'fits.csv');base=read(ROOT/'output/aa-cohort/fits.csv')
    intervals=read(OUT/'intervals.csv');baseint=read(ROOT/'output/aa-cohort/intervals.csv')
    fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained')
    for col,battery in enumerate(('nine','eight')):
        for spec,color in COLORS.items():
            rs=[r for r in (base if spec=='independent' else points) if r['sample']=='all' and r['battery']==battery and (spec=='independent' or r['spec']==spec)]
            irs=[r for r in (baseint if spec=='independent' else intervals) if r['sample']=='all' and r['battery']==battery and (spec=='independent' or r['spec']==spec)]
            axes[0,col].plot(range(3),[float(r['g_variance_share']) for r in rs],'o-',label=spec,color=color)
            for j,r in enumerate(irs):
                if r['low']:axes[0,col].vlines(j,float(r['low']),float(r['high']),color=color,alpha=.6)
            axes[1,col].plot(range(3),[float(r['cfi']) for r in rs],'o-',label=spec,color=color)
        axes[0,col].set(title=battery+' indicators',ylabel='g-attributed task variance',xticks=range(3),xticklabels=HALVES)
        axes[1,col].set(ylabel='CFI',xticks=range(3),xticklabels=HALVES)
        axes[0,col].legend(fontsize=8)
    fig.suptitle('Domain residual covariance: all configurations\n95% conditional base-cluster ranges; exploratory models\nRanges withheld below 90% admissibility')
    fig.savefig(OUT/'domain_cfa.png',dpi=180);plt.close(fig)
    residuals=read(OUT/'domain_correlations.csv')
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for col,battery in enumerate(('nine','eight')):
        rs=[r for r in residuals if r['sample']=='all' and r['battery']==battery and r['spec']=='coding_academic']
        for a,b in sorted({(r['task1'],r['task2']) for r in rs}):
            values=[next(float(r['correlation']) for r in rs if r['task1']==a and r['task2']==b and r['cohort']==h) for h in HALVES]
            axes[col].plot(range(3),values,'o-',label=a+' / '+b)
        axes[col].axhline(0,color='gray',lw=1);axes[col].set(title=battery+' indicators',ylabel='Fitted domain residual correlation',xticks=range(3),xticklabels=HALVES,ylim=(-1,1));axes[col].legend(fontsize=7)
    fig.suptitle('Residual correlations after accounting for g (point estimates)')
    fig.savefig(OUT/'domain_correlations.png',dpi=180);plt.close(fig)


if __name__=='__main__':main()
