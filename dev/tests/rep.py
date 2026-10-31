import json,statistics as S,sys; d=json.load(open(sys.argv[1]))
allm=S.median([v['dps'] for v in d.values()]); print('overall median dps', allm)
cats={}
for k,v in d.items(): cats.setdefault(v['cat'],[]).append((k,v))
for c,l in cats.items():
    print('==',c)
    for k,v in sorted(l,key=lambda x:-x[1]['dps']): print('  %-22s dps %5d (%4.2f)  kills %4d'%(k.replace('skill.',''),v['dps'],v['dps']/allm,v['kills']))
