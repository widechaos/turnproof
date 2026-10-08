import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {evaluateTrace} from '../web/engine.mjs';
const replays=JSON.parse(readFileSync('docs/data/demo.json')).audio_replays.map(x=>x.trace);
const cases=['slow','normal'].map(n=>JSON.parse(readFileSync(`fixtures/${n}-interruption.json`))).concat(replays);
for(const trace of cases){const python=JSON.parse(execFileSync('python3',['-c','import json,sys;from core import evaluate;print(json.dumps(evaluate(json.loads(sys.stdin.read()))))'],{input:JSON.stringify(trace),encoding:'utf8'}));const browser=evaluateTrace(trace);assert.equal(browser.deterministic_pass,python.deterministic_pass);assert.deepEqual(browser.findings,python.findings);}
const bad=structuredClone(cases[0]);bad.events[1].time_ms=NaN;assert.throws(()=>evaluateTrace(bad));
console.log(`Browser/Python verdict and evidence parity verified for ${cases.length} traces`);
