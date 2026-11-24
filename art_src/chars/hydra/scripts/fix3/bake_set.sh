#!/bin/zsh
# usage: bake_set.sh clip...   (bakes work/animfix3_hydra/keys/keys_<clip>.json -> work/animfix3_hydra/act/action_<clip>.json)
cd ~/HerculesGame
W=work/animfix3_hydra
for c in "$@"; do
  tools/ak bake art_src/chars/hydra/hydra.blend --clip $c --keys $W/keys/keys_$c.json --out-action $W/act/action_$c.json > $W/act/bake_$c.log 2>&1
  echo "$c $(tail -1 $W/act/bake_$c.log | python3 -c 'import sys,json;l=sys.stdin.read();d=json.loads(l.split("###AK### ")[1]);print(d.get("ok"),d.get("length"),d.get("loop"),d.get("events"),str(d.get("notes"))[:300], d.get("error"))')"
done
