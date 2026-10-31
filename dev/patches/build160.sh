#!/bin/bash
# EVOLVE v0.16.0 build: repo index.html (0.15.2) → index_v0160.html
set -e
SP=/tmp/claude-0/-home-claude/83fb3698-30c5-58f9-bdc7-80bd93563198/scratchpad
python3 $SP/patch_p160a.py /home/claude/evolve/index.html $SP/v160a.html
python3 $SP/patch_p160b.py $SP/v160a.html $SP/v160b.html
LAST=$SP/v160b.html
for p in c d e; do if [ -f $SP/patch_p160$p.py ]; then python3 $SP/patch_p160$p.py $LAST $SP/v160$p.html; LAST=$SP/v160$p.html; fi; done
python3 $SP/patch_p160z.py $LAST $SP/index_v0160.html
node -e "const fs=require('fs');const h=fs.readFileSync('$SP/index_v0160.html','utf8');const re=/<script[^>]*>([\s\S]*?)<\/script>/g;let m;while((m=re.exec(h))){if(!m[1].trim())continue;try{new Function(m[1]);}catch(e){console.log('SYNTAX',e.message);process.exit(1)}}"
mkdir -p $SP/site16 && cp /home/claude/evolve/*.json /home/claude/evolve/*.png /home/claude/evolve/*.webmanifest /home/claude/evolve/auth.html $SP/site16/ && cp $SP/index_v0160.html $SP/site16/index.html
echo built
