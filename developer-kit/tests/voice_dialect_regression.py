#!/usr/bin/env python3
"""Compare live addon API output with captured Editor PCM, then switch voices.

Requires the local service and the licensed artifacts already in this workspace.
Does not open or modify Anki or the user's A.I.VOICE2 project.
"""
from array import array
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request
import wave

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'notes/evidence/voice-identity'
URL = 'http://127.0.0.1:17862'
AKANE = 'KotonohaAkane_ns_48/KotonohaAkane_ns_48'
AOI = 'KotonohaAoi_ns_48/KotonohaAoi_ns_48'


def speak(text, voice):
    body = json.dumps({'text': text, 'voice': voice}).encode()
    req = urllib.request.Request(URL + '/v1/speak', body,
                                 {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as response:
        data = response.read()
        filename = response.headers['X-Aivoice2-Filename']
        cached = response.headers['X-Aivoice2-Cache']
    with wave.open(io.BytesIO(data)) as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (1, 2, 48000)
        pcm = wav.readframes(wav.getnframes())
    assert pcm
    record = dict(text=text, voice=voice, pcm_bytes=len(pcm),
                  sha256=hashlib.sha256(pcm).hexdigest(), filename=filename, cache=cached)
    return pcm, record


def samples(pcm):
    result = array('h', pcm)
    if sys.byteorder != 'little':
        result.byteswap()
    return result


def main():
    records = []
    originals = {}
    for voice in (AOI, AKANE):
        pcm, record = speak('です。', voice)
        name = voice.split('/')[0]
        gui = (EVIDENCE / ('desu-gui-' + name + '.pcm')).read_bytes()
        assert len(pcm) == len(gui), (voice, len(pcm), len(gui))
        delta = [round(a * 1.06) - b for a, b in zip(samples(pcm), samples(gui))]
        record['gui_gain'] = 1.06
        record['gui_max_delta'] = max(map(abs, delta))
        record['gui_rmse'] = (sum(d * d for d in delta) / len(delta)) ** .5
        assert record['gui_max_delta'] <= 1, record
        originals[voice] = pcm
        records.append(record)
    assert originals[AKANE] != originals[AOI]

    # New text bypasses the audio cache, exercising dialect changes in one worker.
    for text in ('です。です。', 'こんにちは。今日はいい天気ですね。'):
        outputs = []
        for voice in (AOI, AKANE):
            pcm, record = speak(text, voice)
            outputs.append(pcm)
            records.append(record)
        assert outputs[0] != outputs[1], text

    with urllib.request.urlopen(URL + '/v1/voices') as response:
        voices = json.load(response)['voices']
    assert len(voices) == 9
    for item in voices:
        _, record = speak('です。', item['id'])
        record['language'] = item['language']
        records.append(record)
    for voice in (AOI, AKANE):
        pcm, record = speak('です。', voice)
        assert record['cache'] == 'hit'
        assert pcm == originals[voice]
        records.append(record)

    (EVIDENCE / 'dialect-regression.json').write_text(
        json.dumps({'passed': True, 'requests': records}, indent=2, ensure_ascii=False))
    print('PASS: both NV voices match Editor PCM (gain 1.06, max delta 1); '
          'dialect switching, nine voices and cache verified')


if __name__ == '__main__':
    main()
