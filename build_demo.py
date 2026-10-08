"""Export only approved synthetic assets and reports for the public static demo."""
import json
import shutil
from pathlib import Path
from server import demo

ROOT=Path(__file__).parent

def build(destination=ROOT/'docs'):
    destination.mkdir(exist_ok=True)
    for name in ['index.html','style.css','app.js','engine.mjs']:
        shutil.copyfile(ROOT/'web'/name,destination/name)
    (destination/'data').mkdir(exist_ok=True)
    data=demo()
    suite=ROOT/'.runtime/audio-suite/suite.json'
    data['audio_replays']=json.loads(suite.read_text()) if suite.exists() else data['audio_replays']
    # Each record contains synthetic trace/report data only. Never serialize environment/keychain.
    (destination/'data/demo.json').write_text(json.dumps(data,indent=2))
    (destination/'audio').mkdir(exist_ok=True)
    for name in ['change-date','cancel']:
        shutil.copyfile(ROOT/'assets/audio'/(name+'.wav'),destination/'audio'/(name+'.wav'))
    for run in data['audio_replays']:
        name=run['trace']['id']+'-response.wav'
        source = ROOT/'.runtime/audio-suite'/name
        if not source.exists():
            source = ROOT/'assets/audio'/name
        shutil.copyfile(source,destination/'audio'/name)
    (destination/'.nojekyll').touch()
    return data

if __name__=='__main__':
    build()
    print('Static demo exported to docs/; no credentials included')
