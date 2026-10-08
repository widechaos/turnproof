export function evaluateTrace(trace){
 if(!trace||!Array.isArray(trace.events)||!trace.events.length||trace.events.length>1000)throw Error('Trace must contain 1–1000 events');
 if(typeof trace.id!=='string'||typeof trace.source!=='string')throw Error('Trace ID and source must be strings');
 const policy=trace.expectations;if(!policy||typeof policy!=='object')throw Error('Expectations must be an object');
 const budget=policy.interrupt_stop_budget_ms,limits=policy.max_tool_calls;
 if(!Number.isFinite(budget)||budget<0)throw Error('Stop budget must be a finite nonnegative number');
 if(!limits||Array.isArray(limits)||typeof limits!=='object'||Object.values(limits).some(v=>!Number.isInteger(v)||v<0))throw Error('Tool call limits must be nonnegative integers');
 const events=trace.events,ids=new Set();let last=-1;
 for(const e of events){if(!e||typeof e.id!=='string'||ids.has(e.id))throw Error('Every event needs a unique string ID');ids.add(e.id);if(!Number.isFinite(e.time_ms)||e.time_ms<0||e.time_ms<last)throw Error('Timestamps must be finite, nonnegative and ordered');last=e.time_ms;if(typeof e.type!=='string')throw Error('Every event needs a string type');if(e.type==='tool_call'&&typeof e.name!=='string')throw Error('Tool name must be a string');}
 const findings=[],stops=[];let active=false,pending=null;
 for(const e of events){if(e.type==='assistant_audio_start')active=true;else if(e.type==='user_interrupt'&&active&&pending===null)pending=e;else if(e.type==='assistant_audio_stop'){if(pending){const delay=e.time_ms-pending.time_ms;stops.push({delay_ms:delay,evidence:[pending.id,e.id]});if(delay>budget)findings.push({code:'slow_interrupt_stop',value_ms:delay,evidence:[pending.id,e.id]});}active=false;pending=null;}}
 if(pending)findings.push({code:'missing_audio_stop',evidence:[pending.id]});
 const calls=events.filter(e=>e.type==='tool_call'),counts={};for(const e of calls)counts[e.name]=(counts[e.name]||0)+1;
 for(const [name,count] of Object.entries(counts)){if(limits[name]!==undefined&&count>limits[name])findings.push({code:'excess_tool_calls',tool:name,count,evidence:calls.filter(e=>e.name===name).map(e=>e.id)});}
 for(const call of calls){const expected=policy.required_tool_arguments?.[call.name]||{};for(const [key,value] of Object.entries(expected)){const actual=call.arguments?.[key]??null;if(actual!==value)findings.push({code:'wrong_tool_argument',tool:call.name,argument:key,expected:value,actual,evidence:[call.id]});}}
 return {trace_id:trace.id,source:trace.source,deterministic_pass:!findings.length,findings,semantic_evaluation:'not_run',audio_pipeline:trace.provenance?.audio_pipeline||'not_tested',interrupt_stops:stops,tool_calls:counts,events};
}
