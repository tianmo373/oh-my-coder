'use strict';

// electron/voice.js — Whisper speech recognition via @napi-rs/whisper
const path = require('path');
const { readFile } = require('node:fs/promises');

// Lazy-loaded whisper instance
let whisper = null;

async function getWhisper() {
  if (whisper) return whisper;
  
  const { Whisper, decodeAudioAsync } = await import('@napi-rs/whisper');
  
  // Load GGML base model (downloaded to user data dir)
  const modelPath = path.join(process.env.APPDATA || process.env.HOME, '.omc', 'whisper', 'ggml-base.bin');
  const modelBuf = await readFile(modelPath);
  
  whisper = new Whisper(modelBuf);
  return whisper;
}

// Transcribe audio buffer (raw PCM or audio file bytes) to text
async function transcribeAudio(audioBuffer) {
  const { WhisperFullParams, WhisperSamplingStrategy, decodeAudioAsync } = await import('@napi-rs/whisper');
  const w = await getWhisper();
  
  // Decode audio to Float32Array (16kHz mono PCM)
  const pcm = await decodeAudioAsync(audioBuffer, 'input.wav');
  
  // Build params for Chinese transcription
  const params = new WhisperFullParams(WhisperSamplingStrategy.Greedy);
  params.language = 'zh';
  params.printProgress = false;
  params.printRealtime = false;
  params.printTimestamps = false;
  
  // Run full transcription
  const result = w.full(params, pcm);
  
  // full() returns a string directly
  return result || '';
}

module.exports = {
  getWhisper,
  transcribeAudio,
};
