"""Plot separate PCA trajectories without mixing time semantics or measurement units."""
import argparse
import csv
from datetime import datetime
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT=Path(__file__).resolve().parent


def read(path):
    with path.open() as f:return list(csv.DictReader(f))


def plot(out):
    series={r['key']:r for r in read(out/'series.csv')};windows=read(out/'windows.csv');weights=read(out/'loadings.csv')
    available=[k for k,r in series.items() if r['status']=='ok']
    palette=plt.get_cmap('tab10')
    colors={k:palette(i%10) for i,k in enumerate(available)}
    colors.update(aa_nine='#1565c0',aa_eight='#4fa3df',epoch_broad='#bc3c29',epoch_chess='#e38978',estonian='#33895a',livebench='#7545a0')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})

    def decorate(ax,metric):
        ax.grid(alpha=.18);locator=mdates.AutoDateLocator(minticks=3,maxticks=10)
        ax.xaxis.set_major_locator(locator);ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.set_ylim((0,90) if metric=='rotation' else (0,1))
        ax.set_ylabel('Angle from own first window (degrees)' if metric=='rotation' else 'Variance explained by PC1')

    def draw(ax,key,metric,color=None,label=None,style=None):
        rs=sorted((r for r in windows if r['series']==key),key=lambda r:r['date'])
        x=[datetime.fromisoformat(r['date']) for r in rs];y=np.array([float(r[metric]) for r in rs])
        lo=np.array([float(r[metric+'_low']) for r in rs]);hi=np.array([float(r[metric+'_high']) for r in rs])
        color=color or colors[key];limited=series[key]['mode']!='rolling'
        label=label or series[key]['label']+(' (whole panel)' if limited else '')
        ax.plot(x,y,color=color,label=label,lw=1.9,ls=style or ('--' if limited else '-'))
        ax.fill_between(x,lo,hi,color=color,alpha=.12,linewidth=0)
        edge=np.array([r['endpoint_imbalanced']=='True' for r in rs])
        if edge.any():ax.scatter(np.array(x)[edge],y[edge],s=18,facecolors='white',edgecolors=color,zorder=3)

    primary=[k for k in available if series[k]['sensitivity']=='False']
    axes_order=[('release','Release / explicit version dates'),('evaluation','Evaluation dates'),('recorded','Recorded timestamps — semantics unverified')]
    axes_order=[(t,l) for t,l in axes_order if any(series[k]['time_axis']==t for k in primary)]
    fig,axs=plt.subplots(len(axes_order),2,figsize=(15,4.1*len(axes_order)),squeeze=False,layout='constrained')
    for row,(axis,title) in enumerate(axes_order):
        keys=[k for k in primary if series[k]['time_axis']==axis]
        for col,metric in enumerate(('rotation','explained_variance')):
            ax=axs[row,col]
            for k in keys:draw(ax,k,metric)
            decorate(ax,metric);ax.set_title(title+(' · rotation' if col==0 else ' · variance share'),loc='left',fontweight='bold')
        axs[row,0].legend(fontsize=8,loc='upper left',framealpha=.9)
    fig.suptitle('Dominant performance directions over time\nSeparate fixed batteries and source populations; monthly adaptive windows',fontsize=16)
    fig.supxlabel('Calendar date · shaded bands: pointwise 95% cluster-bootstrap intervals · hollow points: temporally unbalanced windows\nEach curve has its own baseline and benchmark scale. Different time axes are not joined; these are not tests of latent-intelligence change.',fontsize=9)
    fig.savefig(out/'rolling-pca.png',dpi=180);fig.savefig(out/'rolling-pca.pdf');plt.close(fig)

    loading_keys=[k for k in available if series[k]['sensitivity']=='False']
    columns=2;rows=(len(loading_keys)+1)//2
    fig,axs=plt.subplots(rows,columns,figsize=(15,4.2*rows),squeeze=False,layout='constrained')
    for ax,key in zip(axs.flat,loading_keys):
        rs=[r for r in weights if r['series']==key and r['date']!='static'];tasks=sorted({r['benchmark'] for r in rs})
        for i,t in enumerate(tasks):
            rr=sorted((r for r in rs if r['benchmark']==t),key=lambda r:r['date'])
            ax.plot([datetime.fromisoformat(r['date']) for r in rr],[float(r['weight']) for r in rr],label=t,lw=1.5,color=plt.get_cmap('tab20')(i%20))
        ax.set_title(series[key]['label'],loc='left',fontweight='bold');ax.set_ylabel('Unit PC1 coefficient');ax.grid(alpha=.18)
        locator=mdates.AutoDateLocator(minticks=3,maxticks=6);ax.xaxis.set_major_locator(locator);ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.legend(fontsize=6.5,ncol=3 if len(tasks)>9 else 2,loc='best',framealpha=.85)
    for ax in list(axs.flat)[len(loading_keys):]:ax.set_visible(False)
    fig.suptitle('Benchmark contributions to the leading performance direction\nFixed source scaling; sign aligned to source-wide PC1',fontsize=16)
    fig.supxlabel('Point estimates; coefficient intervals are in loadings.csv. Batteries stay fixed throughout each series.',fontsize=10)
    fig.savefig(out/'loadings.png',dpi=170);plt.close(fig)

    fig,axs=plt.subplots(2,2,figsize=(15,9),layout='constrained')
    for row,source in enumerate(('AA','Epoch')):
        keys=[k for k in available if series[k]['source']==source]
        for col,metric in enumerate(('rotation','explained_variance')):
            ax=axs[row,col]
            for i,k in enumerate(keys):draw(ax,k,metric,color=palette(i),style='--' if k.endswith('_selected') else '-')
            decorate(ax,metric);ax.set_title(source+(' · rotation' if col==0 else ' · variance share'),loc='left',fontweight='bold')
        axs[row,0].legend(fontsize=8,loc='upper left')
    fig.suptitle('Battery and configuration sensitivities',fontsize=16)
    fig.supxlabel('Solid: all eligible configurations · dashed: one configuration per base/group · bands: pointwise 95% intervals',fontsize=10)
    fig.savefig(out/'sensitivities.png',dpi=180);plt.close(fig)
    print('FIGURES COMPLETE',out,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=ROOT/'output/parallel-rolling-pca');plot(parser.parse_args().out)
