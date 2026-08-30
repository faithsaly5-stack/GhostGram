import os
import asyncio
import wave
import tempfile
import traceback
import subprocess

import imageio_ffmpeg
from google import genai
from google.genai import types

# Get the bundled rock-solid ffmpeg binary path
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

MODEL = "models/gemini-3.5-transcribe-live"
CHUNK_SIZE = 1024

async def transcribe_audio_file(file_path: str, api_keys: list[str], lang_code: str = "fa") -> str:
    """
    Bulletproof speech-to-text engine with API key rotation.
    Converts any audio file to 16kHz Mono 16-bit PCM WAV and transcribes it using Gemini Live.
    """
    if not os.path.exists(file_path):
        return "Error: File not found."
    if not api_keys:
        return "Error: No API keys provided."

    temp_wav_path = None
    try:
        # 1. Flawless audio conversion to 16000Hz, mono, 16-bit PCM WAV using direct ffmpeg
        fd, temp_wav_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        # Run ffmpeg to convert any input format to strict 16kHz mono WAV
        cmd = [
            FFMPEG_EXE, "-y", "-i", file_path, 
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", 
            temp_wav_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()
        
        if process.returncode != 0:
            return f"Error: Audio conversion failed.\n{stderr.decode(errors='ignore')}"
        
        # 2. Connect to API with Rotation Logic
        max_attempts = min(len(api_keys) * 2, 10)
        
        for attempt in range(max_attempts):
            api_key = api_keys[attempt % len(api_keys)]
            key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key
            
            client = genai.Client(
                http_options={"api_version": "v1beta"},
                api_key=api_key,
            )

            config = types.LiveConnectConfig(
                response_modalities=["TEXT"],
                input_audio_transcription=types.AudioTranscriptionConfig(
                    language_auto=types.LanguageAuto(),
                ),
                context_window_compression=types.ContextWindowCompressionConfig(
                    trigger_tokens=104857,
                    sliding_window=types.SlidingWindow(target_tokens=52428),
                ),
            )

            full_transcription = []

            try:
                async with client.aio.live.connect(model=MODEL, config=config) as session:
                    
                    audio_finished = False

                    async def send_audio():
                        nonlocal audio_finished
                        chunk_frames = 16000 
                        with wave.open(temp_wav_path, 'rb') as wf:
                            while True:
                                data = wf.readframes(chunk_frames)
                                if not data:
                                    break
                                await session.send(input={"data": data, "mime_type": "audio/pcm;rate=16000"})
                                await asyncio.sleep(0.05)
                                
                        await session.send(input=".", end_of_turn=True)
                        audio_finished = True

                    async def receive_transcription():
                        async for response in session.receive():
                            sc = getattr(response, "server_content", None)
                            if sc is not None:
                                transcription_obj = getattr(sc, "input_transcription", None)
                                if transcription_obj is not None and getattr(transcription_obj, "text", ""):
                                    full_transcription.append(transcription_obj.text.strip())
                                    
                                model_turn = getattr(sc, "model_turn", None)
                                if model_turn is not None:
                                    for part in getattr(model_turn, "parts", []):
                                        if getattr(part, "text", ""):
                                            full_transcription.append(part.text.strip())
                                
                                # Only break if audio is fully uploaded AND the server finished generating
                                if audio_finished and (getattr(sc, "turn_complete", False) or getattr(sc, "generation_complete", False)):
                                    break

                    async with asyncio.TaskGroup() as tg:
                        tg.create_task(send_audio())
                        tg.create_task(receive_transcription())

                return " ".join(full_transcription).strip()

            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                    print(f"⏳ Key {key_preview} hit rate limit on live transcribe. Rotating...")
                    continue
                elif "403" in err_str or "api_key_invalid" in err_str:
                    print(f"❌ Key {key_preview} is invalid. Rotating...")
                    continue
                else:
                    print(f"⚠️ Unknown error on live transcribe with key {key_preview}: {e}. Rotating...")
                    continue
                    
        return "Error: All keys exhausted or failed during transcription."

    except Exception as e:
        traceback.print_exc()
        return f"Error during audio processing: {str(e)}"
    finally:
        # 3. Cleanup
        if temp_wav_path and os.path.exists(temp_wav_path):
            try:
                os.remove(temp_wav_path)
            except:
                pass
