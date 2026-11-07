"""Render PCA cohort comparisons from saved estimates; no PCA refits."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT=Path(__file__).resolve().parent/'output/aa-pca'
HALVES=('2025H1','2025H2','2026H1')
PAIRS=(('2025H1','2025H2'),('2025H2','2026H1'),('2025H1','2026H1'))
COLORS={'nine':'#d95f0e','eight':'#225ea8'}


def read(name):return list(csv.DictReader((OUT/name).open()))


def main():
    sims=read('similarities.csv');variance=read('explained_variance.csv')
    fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained')
    for col,sample in enumerate(('all','selected')):
        for battery,color in COLORS.items():
            offset=-.05 if battery=='nine' else .05
            rs=[next(r for r in sims if r['sample']==sample and r['battery']==battery and r['metric']=='angle_degrees' and r['cohort_a']==a and r['cohort_b']==b) for a,b in PAIRS]
            x=np.arange(3)+offset
            axes[0,col].plot(x,[float(r['point']) for r in rs],'o',color=color,label=battery+' indicators')
            for xx,r in zip(x,rs):
                if r['low']:axes[0,col].vlines(xx,float(r['low']),float(r['high']),color=color)
            rs=[next(r for r in variance if r['sample']==sample and r['battery']==battery and r['cohort']==h) for h in HALVES]
            axes[1,col].plot(x,[float(r['point']) for r in rs],'o-',color=color)
            for xx,r in zip(x,rs):
                if r['low']:axes[1,col].vlines(xx,float(r['low']),float(r['high']),color=color)
        axes[0,col].set(title='All configurations' if sample=='all' else 'One configuration per named base',ylabel='PC1 axis angle (degrees)',xticks=range(3),xticklabels=['25H1 / 25H2','25H2 / 26H1','25H1 / 26H1'],ylim=(0,45));axes[0,col].legend()
        axes[1,col].set(ylabel='PC1 fraction of cohort variance',xticks=range(3),xticklabels=HALVES,ylim=(.6,.9))
    fig.suptitle('PC1 direction versus explained variance\nOne frozen pooled benchmark metric; 2,000 matched named-base cluster draws\nNominal percentile ranges; no directional equality/equivalence test')
    fig.savefig(OUT/'pca_comparisons.png',dpi=180);plt.close(fig)
    rs=read('weight_intervals.csv');fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for battery,ax in zip(('nine','eight'),axes):
        tasks=[r['task'] for r in rs if r['sample']=='all' and r['battery']==battery and r['cohort']=='2025H1']
        for g,(h,color) in enumerate(zip(HALVES,('#225ea8','#41ab5d','#d95f0e'))):
            rows=[next(r for r in rs if r['sample']=='all' and r['battery']==battery and r['cohort']==h and r['task']==t) for t in tasks]
            x=np.arange(len(tasks))+(g-1)*.14
            ax.plot(x,[float(r['point']) for r in rows],'o-',color=color,label=h,alpha=.9)
            for xx,r in zip(x,rows):
                if r['low']:ax.vlines(xx,float(r['low']),float(r['high']),color=color,alpha=.6)
        ax.set(title=battery+' indicators',ylabel='Unit PC1 coefficient in common pooled units',xticks=range(len(tasks)),xticklabels=tasks,ylim=(0,.65));ax.tick_params(axis='x',labelrotation=70);ax.legend()
    fig.suptitle('How the dominant direction is weighted: all configurations\nSigns aligned to positive performance; nominal marginal 95% cluster ranges')
    fig.savefig(OUT/'pca_weights.png',dpi=180);plt.close(fig)


if __name__=='__main__':main()
