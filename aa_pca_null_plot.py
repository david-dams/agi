"""Render saved common-axis null distributions without rerunning simulations."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent/'output/aa-pca-null'


def main():
    b=np.load(OUT/'null_distributions.npz');tests=list(csv.DictReader((OUT/'calibrated_tests.csv').open()));cases=b['cases']
    fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained')
    colors=('#225ea8','#41ab5d');bins=np.linspace(0,45,75)
    for c,(sample,battery) in enumerate(cases):
        ax=axes.flat[c]
        for s,scheme in enumerate(b['schemes']):
            for m,method in enumerate(b['methods']):
                a=b['angles'][s,m,:,c,2];a=a[np.isfinite(a)]
                ax.hist(a,bins=bins,density=True,histtype='step' if s else 'stepfilled',alpha=1 if s else .3,
                    linestyle='--' if s else '-',color=colors[m],label=method+(' / global' if s else ' / fixed N'))
        r=next(r for r in tests if r['sample']==sample and r['battery']==battery and r['scheme']=='fixed_sizes' and r['method']=='projected' and r['comparison']=='2025H1 / 2026H1')
        ax.axvline(float(r['observed']),color='#d95f0e',lw=2,label='observed')
        ax.set(title=f'{sample}/{battery}',xlabel='First-to-last PC1 angle (degrees)',ylabel='Null density',xlim=(0,45))
        if c==0:ax.legend(fontsize=7)
    fig.suptitle('Shared-PC1 null: observed first-to-last rotation versus cluster sampling\n2,000 draws per null/sampling design; common benchmark units')
    fig.savefig(OUT/'first_last_nulls.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained')
    pairs=('2025H1 / 2025H2','2025H2 / 2026H1','2025H1 / 2026H1')
    for c,(sample,battery) in enumerate(cases):
        ax=axes.flat[c]
        for m,method in enumerate(b['methods']):
            rs=[next(r for r in tests if r['sample']==sample and r['battery']==battery and r['scheme']=='fixed_sizes' and r['method']==method and r['comparison']==pair) for pair in pairs]
            q95=np.array([float(r['null_q95']) for r in rs]);q99=np.array([float(r['null_q99']) for r in rs])
            ax.plot(range(3),q95,'o--',color=colors[m],label=method+' q95');ax.fill_between(range(3),q95,q99,color=colors[m],alpha=.15,label=method+' q95–q99')
        ax.plot(range(3),[float(r['observed']) for r in rs],'o-',color='#d95f0e',lw=2,label='observed')
        ax.set(title=f'{sample}/{battery}',xticks=range(3),xticklabels=['25H1 / 25H2','25H2 / 26H1','25H1 / 26H1'],ylabel='Axis angle (degrees)',ylim=(0,45))
        if c==0:ax.legend(fontsize=7)
    fig.suptitle('Pairwise observed angles and fixed-size shared-axis null percentiles\nTail comparisons are conditional on null construction and named-base resampling')
    fig.savefig(OUT/'pairwise_null_percentiles.png',dpi=180);plt.close(fig)


if __name__=='__main__':main()
