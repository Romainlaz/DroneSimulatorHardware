import sys,glob,os
import numpy as np
from pyulog import ULog
pat=sys.argv[1:] or ['test_20261103_*','test_20261104_*']
os.chdir(os.path.expanduser('~/drone-tools/logs'))
print('run|imu>6%|imu>20n|imuMax|cpu load moy|gt sd|gt min|gt max|err moy|err maxabs|est sd|baro innov sd|baro rej%|gps hgt rej%|hgt ratio max|ev flags|hover_thr sd|armement t(s)|baro_bias')
for p in pat:
 for d in sorted(glob.glob(p)):
    fs=glob.glob(d+'/*.ulg')
    if not fs: continue
    u=ULog(fs[0]);D=lambda n:u.get_dataset(n).data
    pos=D('vehicle_local_position');g=D('vehicle_local_position_groundtruth');L=D('vehicle_land_detected')
    t=pos['timestamp']/1e6;z=-pos['z'];zg=np.interp(t,g['timestamp']/1e6,-g['z'])
    fl=L['timestamp'][L['landed']==0]/1e6
    t0,t1=fl[0]+8,fl[-1]-5;m=(t>t0)&(t<t1)
    dt=np.diff(D('sensor_combined')['timestamp'])/1e3
    cl=D('cpuload')['load'].mean()
    err=z-zg
    b=D('estimator_aid_src_baro_hgt');bt=b['timestamp']/1e6;bm=(bt>t0)&(bt<t1)
    gh=D('estimator_aid_src_gnss_hgt');gt=gh['timestamp']/1e6;gm=(gt>t0)&(gt<t1)
    st=D('vehicle_status');arm=st['timestamp'][st['arming_state']==2][0]/1e6-u.start_timestamp/1e6
    try:
        h=D('hover_thrust_estimate');ht=h['timestamp']/1e6;hs=h['hover_thrust'][(ht>t0)&(ht<t1)].std()
    except Exception: hs=float('nan')
    try:
        bb=D('estimator_baro_bias');bbv=bb['bias'][-1]
    except Exception: bbv=float('nan')
    print(d[5:],'%.2f|%d|%.0f|%.2f|%.3f|%.2f|%.2f|%.3f|%.3f|%.3f|%.3f|%.1f|%.1f|%.2f|%d|%.4f|%.1f|%.3f'%(100*(dt>6).mean(),(dt>20).sum(),dt.max(),cl,zg[m].std(),zg[m].min(),zg[m].max(),err[m].mean(),np.abs(err[m]).max(),z[m].std(),b['innovation'][bm].std(),100*b['innovation_rejected'][bm].mean(),100*gh['innovation_rejected'][gm].mean(),max(b['test_ratio'][bm].max(),gh['test_ratio'][gm].max()),0,hs,arm,bbv),sep='|')
