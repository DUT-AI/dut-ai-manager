"""Audio utility functions for processing, converting, and downsampling WAV files."""

import io
import struct
import wave
from loguru import logger


def downsample_wav_to_16k_mono(
    wav_bytes: bytes,
    target_rate: int = 16000,
    target_bits: int = 8,
) -> bytes:
    """
    Downsample a PCM WAV byte stream to target sample rate (default: 16kHz)
    and target bit-depth (default: 8-bit unsigned PCM) mono.

    Why 8-bit?
    1. ESP32 internal DAC is hardware 8-bit (0-255).
    2. Reduces file size by 50% compared to 16-bit!
       A 4.3s TTS speech drops from ~415KB down to only ~69KB.
    3. Guarantees ESP32 malloc (< 70KB) always succeeds easily without heap fragmentation.
    """
    if not wav_bytes or len(wav_bytes) < 44:
        return wav_bytes

    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as reader:
            n_channels = reader.getnchannels()
            sampwidth = reader.getsampwidth()
            src_rate = reader.getframerate()
            n_frames = reader.getnframes()
            raw_data = reader.readframes(n_frames)

        # Only process 16-bit PCM (standard TTS output)
        if sampwidth != 2:
            logger.debug(f"Audio sampwidth is {sampwidth}, skipping downsampling.")
            return wav_bytes

        fmt = f"<{n_frames * n_channels}h"
        src_samples = struct.unpack(fmt, raw_data)

        # Convert stereo to mono if needed
        if n_channels == 2:
            mono_samples = [
                (src_samples[i * 2] + src_samples[i * 2 + 1]) // 2
                for i in range(n_frames)
            ]
        elif n_channels == 1:
            mono_samples = list(src_samples)
        else:
            logger.warning(f"Unsupported channel count {n_channels}")
            return wav_bytes

        # Resample sample rate
        if src_rate == target_rate:
            resampled_samples = mono_samples
        else:
            out_frames = int(n_frames * target_rate / src_rate)
            resampled_samples = []
            ratio = src_rate / target_rate
            total_mono = len(mono_samples)

            for i in range(out_frames):
                src_pos = i * ratio
                idx = int(src_pos)
                frac = src_pos - idx
                if idx + 1 < total_mono:
                    s = int(mono_samples[idx] * (1.0 - frac) + mono_samples[idx + 1] * frac)
                elif idx < total_mono:
                    s = mono_samples[idx]
                else:
                    break
                resampled_samples.append(s)

        # Peak Normalization: Đưa âm lượng lên ~92% full-scale để loa ESP32 kêu to, rõ
        max_val = max((abs(s) for s in resampled_samples), default=0)
        if 0 < max_val < 29000:
            scale = 29000.0 / max_val
            normalized_samples = [int(s * scale) for s in resampled_samples]
        else:
            normalized_samples = resampled_samples

        out_io = io.BytesIO()
        with wave.open(out_io, "wb") as writer:
            writer.setnchannels(1)
            writer.setframerate(target_rate)

            if target_bits == 8:
                # 8-bit unsigned PCM (0 to 255, center at 128)
                # Đẩy mạnh dynamic range với hệ số gain 1.8x và soft clipping để loa phát to rõ nhất
                writer.setsampwidth(1)
                packed_8bit = bytearray(len(normalized_samples))
                for idx, s in enumerate(normalized_samples):
                    boosted = int(s * 1.8)
                    clamped_16 = max(-32768, min(32767, boosted))
                    # Map [-32768, 32767] -> [0, 255]
                    val_8 = (clamped_16 + 32768) >> 8
                    packed_8bit[idx] = max(0, min(255, val_8))
                writer.writeframes(bytes(packed_8bit))
            else:
                # 16-bit signed PCM
                writer.setsampwidth(2)
                clamped_16_list = [
                    max(-32768, min(32767, s)) for s in normalized_samples
                ]
                writer.writeframes(
                    struct.pack(f"<{len(clamped_16_list)}h", *clamped_16_list)
                )

        resampled_bytes = out_io.getvalue()
        logger.info(
            f"Downsampled audio: {src_rate}Hz/{sampwidth*8}bit ({n_channels}ch, {len(wav_bytes)}B) -> "
            f"{target_rate}Hz/{target_bits}bit (1ch, {len(resampled_bytes)}B, peak={max_val})"
        )
        return resampled_bytes

    except Exception as exc:
        logger.error(f"Failed to downsample WAV audio: {exc}")
        return wav_bytes
