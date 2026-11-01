#!/bin/bash
set -e
SP=/tmp/claude-0/-home-claude/83fb3698-30c5-58f9-bdc7-80bd93563198/scratchpad
python3 $SP/patch_p180a.py /home/claude/evolve/index.html $SP/v180a.html
python3 $SP/patch_p180b.py $SP/v180a.html $SP/v180b.html
python3 $SP/patch_p180c.py $SP/v180b.html $SP/v180c.html
python3 $SP/patch_p180d.py $SP/v180c.html $SP/v180d.html
python3 $SP/patch_p180z.py $SP/v180d.html $SP/index_v0180.html
node -e "const fs=require('fs');const a=require('$SP/node_modules/acorn');const h=fs.readFileSync('$SP/index_v0180.html','utf8');const re=/<script[^>]*>([\s\S]*?)<\/script>/g;let m,bad=0;while((m=re.exec(h))){if(!m[1].trim())continue;try{a.parse(m[1],{ecmaVersion:2022})}catch(e){bad=1;const L=m[1].split('\n');console.log('SYNTAX',e.message, L[e.loc.line-1].slice(Math.max(0,e.loc.column-150),e.loc.column+60))}}process.exit(bad)"
rm -rf $SP/site180 && cp -r $SP/site174 $SP/site180 && cp $SP/index_v0180.html $SP/site180/index.html
echo built
