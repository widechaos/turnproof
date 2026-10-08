"""Measured file-based audio replay through Whisper and a reference voice agent.

This measures batch processing, not streaming barge-in or human experience.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
from audio import transcribe
from core import evaluate
from reference_agent import respond


def replay(wav, model, case, fault='none', source='synthetic_voice', synthesize=None):
    start = time.monotonic()
    events, bookings = [], []
    def emit(kind, **data):
        events.append({'id': 'e' + str(len(events)+1),
                       'time_ms': round((time.monotonic()-start)*1000), 'type': kind, **data})
    emit('input_audio_loaded', sha256=hashlib.sha256(wav.read_bytes()).hexdigest())
    speech = transcribe(wav, model, source)
    text = ' '.join(s['text'].strip() for s in speech['transcript'])
    emit('user_transcript', text=text)
    def tool(name, arguments):
        bookings.append(dict(arguments))
        emit('tool_call', name=name, arguments=arguments)
    response = respond(text, tool, fault)
    emit('assistant_text', text=response)
    if synthesize:
        output = synthesize(response)
        emit('response_audio_written', file=output.name)
    limits = {'save_booking': 0 if case == 'cancel' else 1}
    expected_args = {'save_booking': {'date': 'Friday'}} if case == 'change-date' else {}
    trace = {'id': case+'-'+fault, 'source': source,
             'expectations': {'interrupt_stop_budget_ms': 250, 'max_tool_calls': limits,
                              'semantic_goal': 'Cancel without saving any booking.' if case == 'cancel'
                                               else 'Save the booking for Friday, never Thursday.',
                              'required_tool_arguments': expected_args},
             'events': events,
             'provenance': {'agent': 'offline_reference_booking_agent', 'fault_mode': fault,
                            'audio_pipeline': 'file_asr_agent_tts' if synthesize else 'file_asr_agent',
                            'streaming_barge_in': 'not_tested', 'human_trial': False}}
    report = evaluate(trace)
    report['audio_pipeline'] = trace['provenance']['audio_pipeline']
    return {'trace': trace, 'report': report, 'test_bookings': bookings,
            'response': response, 'processing_ms': round((time.monotonic()-start)*1000)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('wav', type=Path)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--case', required=True, choices=['cancel', 'change-date'])
    parser.add_argument('--fault', default='none', choices=['none', 'ignore_cancel', 'wrong_date', 'duplicate_save'])
    parser.add_argument('--source', default='synthetic_voice', choices=['synthetic_voice', 'authorized_human_recording'])
    args = parser.parse_args()
    print(json.dumps(replay(args.wav, args.model, args.case, args.fault, args.source), indent=2))
