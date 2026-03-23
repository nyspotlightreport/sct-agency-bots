#!/usr/bin/env python3
"""
agents/voice_ai/__init__.py
ProFlow Voice AI Platform — Core Architecture
Rivals: ElevenLabs, Vapi, Retell, Bland AI, Cartesia, PolyAI

ARCHITECTURE:
┌─────────────────────────────────────────────────┐
│              ProFlow Voice AI Platform           │
├──────────┬──────────┬──────────┬────────────────┤
│ STT      │ LLM      │ TTS      │ Telephony      │
│ Deepgram │ Claude   │ Eleven   │ Twilio         │
│ Whisper  │ GPT-4o   │ OpenAI   │ WebSocket      │
│          │          │ Cartesia │ SIP/PSTN       │
├──────────┴──────────┴──────────┴────────────────┤
│ Voice Cloning │ Emotion │ Multilingual │ CRM     │
│ ElevenLabs    │ Hume    │ 29 languages │ Supa    │
├─────────────────────────────────────────────────┤
│ Specialized Agents                               │
│ Sales │ Support │ Receptionist │ Medical │ Legal │
└─────────────────────────────────────────────────┘

COMPETITIVE ADVANTAGES:
- Multi-provider: Falls back between STT/TTS providers for 99.99% uptime
- Sub-500ms latency: Streaming STT → LLM → TTS pipeline
- Voice cloning: Clone any voice in 30 seconds of audio
- 29 languages: Full conversational AI in any language
- Specialized agents: Pre-trained for sales, support, medical, legal
- Full CRM integration: Every call logged, transcribed, analyzed
- Self-improving: Claude analyzes calls and improves scripts
"""
VERSION = "1.0.0"
PLATFORM_NAME = "ProFlow Voice AI"
