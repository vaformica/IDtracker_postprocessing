"""Collect all outcomes; failed runs remain visible, never treated as zero missing."""
from pathlib import Path
import csv,json,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
ROOT=Path(__file__).resolve().parent

def main():
    tasks=json.loads((ROOT/'tasks.json').read_text());rows=[]
    for task in tasks:
        folder=ROOT/'runs'/task['name'];row=dict(task)
        if (folder/'metrics.json').exists():row.update(json.loads((folder/'metrics.json').read_text()))
        status=json.loads((folder/'status.json').read_text()) if (folder/'status.json').exists() else {'stage':'NO_STATUS'}
        row['status']=status['stage'];row['error']=status.get('error','');rows.append(row)
    out=ROOT/'comparison';out.mkdir(exist_ok=False)
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with (out/'all_runs.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    consensus=[]
    for bg in [False,True]:
        for threshold in ([30,50,70] if bg else [123,143,163]):
            for area in [250,400,550]:
                group=[r for r in rows if r['kind']=='shared_grid' and r['use_bkg']==bg and r['min_area']==area and r['intensity_low' if bg else 'intensity_high']==threshold]
                complete=[r for r in group if r['status']=='COMPLETE_UNREVIEWED']
                score=sum(r['missing_percent']*(1 if r['label']=='Box02_MIX' else .5) for r in complete)/2 if len(complete)==3 else None
                consensus.append(dict(use_bkg=bg,threshold=threshold,min_area=area,completed=len(complete),weighted_missing_percent=score,
                    worst_missing_percent=max(r['missing_percent'] for r in complete) if complete else None,
                    minimum_estimated_accuracy=min(r['estimated_accuracy'] for r in complete) if complete and all(r.get('estimated_accuracy') is not None for r in complete) else None))
    with (out/'consensus.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(consensus[0]));w.writeheader();w.writerows(consensus)
    labels=['Box01_OLD','Box01_OLD_TEst','Box02_MIX']
    with PdfPages(out/'grid_comparison.pdf') as pdf:
        fig=plt.figure(figsize=(11.7,8.3));fig.suptitle('Charlotte trial01: 60-run IDtracker parameter sweep',fontsize=20,y=.94)
        controls=[r for r in rows if r['kind']=='paired_control']
        cells=[[r['label'],'on' if r['use_bkg'] else 'off',str([r['intensity_low'],r['intensity_high']]),r['min_area'],f"{r['missing_percent']:.2f}" if 'missing_percent' in r else 'NA',r['status']] for r in controls]
        ax=fig.add_axes([.04,.35,.92,.45]);ax.axis('off');table=ax.table(cellText=cells,colLabels=['Source','Background','Intensity','Min area','Missing %','Status'],loc='center',cellLoc='center');table.auto_set_font_size(False);table.set_fontsize(9);table.scale(1,1.8)
        fig.text(.06,.23,f"Completed reports: {sum(r['status']=='COMPLETE_UNREVIEWED' for r in rows)}/60. Evaluation: frames422-7622, six IDs, 43,206 coordinate opportunities.",fontsize=11)
        fig.text(.06,.13,'Controls toggle background only; all tracking intervals standardized to [422,16998].\nMissingness uses original IDtracker coordinates, which may already include gap filling.\nOLD and OLD_TEst describe the same group. None of these outputs is manually validated.',fontsize=10)
        pdf.savefig(fig);plt.close(fig)
        for bg in [False,True]:
            fig,axes=plt.subplots(1,3,figsize=(11.7,8.3));fig.suptitle('Raw missing-coordinate % | background '+('on' if bg else 'off'),fontsize=19,y=.93)
            thresholds=[30,50,70] if bg else [123,143,163]
            for label,ax in zip(labels,axes):
                values=np.full((3,3),np.nan)
                for r in rows:
                    if r['kind']=='shared_grid' and r['label']==label and r['use_bkg']==bg and 'missing_percent' in r:
                        values[[250,400,550].index(r['min_area']),thresholds.index(r['intensity_low' if bg else 'intensity_high'])]=r['missing_percent']
                ax.imshow(values,vmin=0,vmax=100,cmap='viridis_r');ax.set_title(label);ax.set_xticks(range(3),thresholds);ax.set_yticks(range(3),[250,400,550]);ax.set_xlabel('Lower cutoff (to255)' if bg else 'Upper cutoff (from0)');ax.set_ylabel('Minimum blob area (pixels²)')
                for (i,j),value in np.ndenumerate(values):ax.text(j,i,f'{value:.1f}' if np.isfinite(value) else 'FAILED',ha='center',va='center',color='white' if not np.isfinite(value) or value<50 else 'black')
            fig.text(.06,.15,'NA/FAILED cells are unavailable, not zero. Lower missingness alone does not establish better segmentation or identity accuracy.',fontsize=10)
            fig.subplots_adjust(left=.07,right=.97,bottom=.25,top=.80,wspace=.38);pdf.savefig(fig);plt.close(fig)
        fig=plt.figure(figsize=(11.7,8.3));fig.suptitle('Shared-setting shortlist: descriptive, pending visual validation',fontsize=18,y=.94)
        ranked=sorted([r for r in consensus if r['completed']==3],key=lambda r:r['weighted_missing_percent'])[:10]
        ax=fig.add_axes([.05,.25,.9,.55]);ax.axis('off')
        cells=[['on' if r['use_bkg'] else 'off',r['threshold'],r['min_area'],f"{r['weighted_missing_percent']:.2f}",f"{r['worst_missing_percent']:.2f}",f"{100*r['minimum_estimated_accuracy']:.2f}" if r['minimum_estimated_accuracy'] is not None else 'NA'] for r in ranked]
        if cells:
            table=ax.table(cellText=cells,colLabels=['Background','Cutoff','Min area','Weighted missing %','Worst missing %','Min IDtracker accuracy %'],loc='center',cellLoc='center');table.auto_set_font_size(False);table.set_fontsize(10);table.scale(1,1.8)
        else:ax.text(.1,.5,'No parameter combination completed across all three configurations.')
        fig.text(.06,.13,'Weighting: OLD 25%, OLD_TEst 25%, MIX 50%; this avoids counting OLD twice as independent biology.\nRanking is a screening aid only. Inspect blobs, identity assignments, and contact gaps before choosing defaults.\nAll failures, silhouette scores, crossing-blob counts, jump rates, and settings are retained in all_runs.csv.',fontsize=10)
        pdf.savefig(fig);plt.close(fig)
    (out/'status.json').write_text(json.dumps({'stage':'COMPLETE_UNREVIEWED','completed':sum(r['status']=='COMPLETE_UNREVIEWED' for r in rows),'total':60},indent=2)+'\n')
if __name__=='__main__':main()
