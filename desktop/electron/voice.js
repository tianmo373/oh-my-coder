'use strict';

// electron/voice.js — Whisper speech recognition via @napi-rs/whisper
const path = require('path');

// Lazy-loaded whisper instance
let whisper = null;

async function getWhisper() {
  if (whisper) return whisper;
  
  // @napi-rs/whisper works in main process
  const { Whisper } = await import('@napi-rs/whisper');
  
  // Load GGML base model (downloaded to user data dir)
  const modelPath = path.join(process.env.APPDATA || process.env.HOME, '.omc', 'whisper', 'ggml-base.bin');
  
  whisper = new Whisper(modelPath);
  return whisper;
}

// Transcribe audio buffer to text
async function transcribeAudio(audioBuffer) {
  const w = await getWhisper();
  
  // audioBuffer should be Float32Array or Int16Array of 16kHz mono PCM
  const result = w.transcribe(audioBuffer, {
    language: 'zh',
  });
  
  return result.text || '';
}

module.exports = {
  getWhisper,
  transcribeAudio,
};