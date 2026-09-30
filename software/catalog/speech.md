# Speech

Speech-to-text and text-to-speech that run locally. 8 projects; 7 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

A code license says nothing about model weights or voices, which often carry their own terms; read each model card. Clone a voice only with its owner's consent.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | copy | MIT | C++ | 54046 | 2026-09-28 | Whisper speech-to-text in plain C/C++; fast on ordinary CPUs and consumer GPUs with no Python stack. |
| [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox) | copy | MIT | Python | 26628 | 2026-07-21 | Open text-to-speech models, including a multilingual one, with voice cloning from a short reference clip. |
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | copy | MIT | Python | 25649 | 2026-09-30 | Whisper reimplemented on CTranslate2, several times faster with less memory; the engine inside many transcription tools. |
| [m-bain/whisperX](https://github.com/m-bain/whisperX) | copy | BSD-2-Clause | Python | 24319 | 2026-09-26 | Adds word-level timestamps and speaker labels on top of Whisper, which is what subtitles and meeting transcripts need. |
| [hexgrad/kokoro](https://github.com/hexgrad/kokoro) | copy | Apache-2.0 | JavaScript | 9095 | 2025-08-06 | Small text-to-speech model (about 82M parameters) with natural voices that runs quickly on a CPU. |
| [speaches-ai/speaches](https://github.com/speaches-ai/speaches) | copy | MIT | Python | 3693 | 2026-09-29 | OpenAI-compatible server for local speech-to-text and text-to-speech, so apps written for the cloud audio API can point at your own machine. |
| [thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) | copy (see note) | MIT | Python | 2749 | 2026-09-01 | Runs the Kokoro-82M text-to-speech model through ONNX Runtime on an ordinary CPU with a small Python API; model files download separately. **ONNX Runtime's official builds turn telemetry on by default; set `ORT_DISABLE_TELEMETRY=1` before it loads (Linux and macOS); the Kokoro-82M weights are Apache-2.0 per their model card; two dependencies are GPL-3.0: phonemizer, and the espeak-ng library that espeakng-loader bundles** |
| [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) | study only | GPL-3.0 | C++ | 5730 | 2026-09-28 | Maintained successor to Piper, a fast text-to-speech engine that runs on a CPU. |
