"""Transcribe an authorized or synthetic WAV locally using whisper.cpp."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

def transcribe(wav, model, source):
    if source not in ('synthetic_voice', 'authorized_human_recording'):
        raise ValueError('Audio source must be declared')
    if not wav.is_file() or not model.is_file():
        raise ValueError('Audio and model must exist')
    with tempfile.TemporaryDirectory() as directory:
        converted = Path(directory) / 'input.wav'
        prefix = Path(directory) / 'transcript'
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(wav),
            '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', str(converted)], check=True)
        subprocess.run(['whisper-cli', '-m', str(model), '-f', str(converted),
            '-l', 'en', '-oj', '-of', str(prefix)], check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        data = json.loads(prefix.with_suffix('.json').read_text())
        return {'source': source, 'audio_pipeline': 'local_transcription_completed',
                'transcript': data.get('transcription', []), 'agent_replay': 'not_run'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('wav', type=Path)
    parser.add_argument('--model', required=True, type=Path)
    parser.add_argument('--source', required=True, choices=['synthetic_voice', 'authorized_human_recording'])
    args = parser.parse_args()
    print(json.dumps(transcribe(args.wav, args.model, args.source), indent=2))
