"""Run original audio through a reference agent and render its responses locally."""
import argparse
import json
from pathlib import Path
from replay import replay


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--whisper-model', type=Path, required=True)
    parser.add_argument('--tts-model', type=Path, required=True)
    parser.add_argument('--voices', type=Path, required=True)
    parser.add_argument('--audio-dir', type=Path, default=Path('assets/audio'))
    parser.add_argument('--output', type=Path, default=Path('.runtime/audio-suite'))
    args = parser.parse_args()
    from kokoro_onnx import Kokoro
    import soundfile as sf
    engine = Kokoro(str(args.tts_model), str(args.voices))
    args.output.mkdir(parents=True, exist_ok=True)
    suite=[]
    for case, fault in [('change-date','none'), ('change-date','wrong_date'),
                        ('cancel','none'), ('cancel','ignore_cancel')]:
        name = case+'-'+fault
        def synthesize(text):
            samples, rate = engine.create(text, voice='af_heart', lang='en-us')
            path = args.output/(name+'-response.wav')
            sf.write(str(path), samples, rate)
            return path
        result = replay(args.audio_dir/(case+'.wav'), args.whisper_model, case, fault,
                        synthesize=synthesize)
        (args.output/(name+'.json')).write_text(json.dumps(result,indent=2))
        suite.append(result)
        print(name, 'PASS' if result['report']['deterministic_pass'] else 'FAIL',
              result['processing_ms'], 'ms', flush=True)
    (args.output/'suite.json').write_text(json.dumps(suite,indent=2))


if __name__ == '__main__':
    main()
