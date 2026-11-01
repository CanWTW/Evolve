#!/bin/bash
set -e
SP=/tmp/claude-0/-home-claude/83fb3698-30c5-58f9-bdc7-80bd93563198/scratchpad
python3 $SP/patch_p181.py /home/claude/evolve/index.html $SP/index_v0181.html
node -e "const fs=require('fs');const a=require('$SP/node_modules/acorn');const h=fs.readFileSync('$SP/index_v0181.html','utf8');const re=/<script[^>]*>([\s\S]*?)<\/script>/g;let m,bad=0;while((m=re.exec(h))){if(!m[1].trim())continue;try{a.parse(m[1],{ecmaVersion:2022})}catch(e){bad=1;const L=m[1].split('\n');console.log('SYNTAX',e.message, L[e.loc.line-1].slice(Math.max(0,e.loc.column-150),e.loc.column+60))}}process.exit(bad)"
rm -rf $SP/site181 && cp -r $SP/site180 $SP/site181 && cp $SP/index_v0181.html $SP/site181/index.html
echo built
