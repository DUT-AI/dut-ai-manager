"""Text-to-Speech (TTS) Service using external Zerotts API."""

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import aiohttp
from loguru import logger

from app.core.config import settings

# Default API Configuration & Hyperparameters
DEFAULT_TTS_API_URL = "https://tts.dutai.io.vn/v1/audio/speech"
DEFAULT_MODEL = "zerotts"
DEFAULT_VOICE = "hamy"
DEFAULT_RESPONSE_FORMAT = "wav"
DEFAULT_SPEED = 1.0
DEFAULT_NORMALIZE_TEXT = True
DEFAULT_CFG_SCALE = 1.0
DEFAULT_AUDIO_TEMPERATURE = 0.8
DEFAULT_AUDIO_TOPK = 25
DEFAULT_AUDIO_TOPP = 0.95
DEFAULT_AUDIO_REPETITION_PENALTY = 1.2
DEFAULT_TIMEOUT_SECONDS = 60.0


class TTSServiceError(Exception):
    """Custom exception for TTS service errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: Any = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class TTSService:
    """
    Service for converting text to speech using external TTS endpoint.
    Supports audio generation, streaming, saving to disk, and MinIO upload.
    """

    FORMAT_MIME_MAP = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "opus": "audio/opus",
        "aac": "audio/aac",
        "flac": "audio/flac",
        "pcm": "audio/pcm",
    }

    def __init__(
        self,
        api_url: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        configured_url = getattr(settings, "TTS_API_URL", DEFAULT_TTS_API_URL)
        self.api_url = api_url or configured_url or DEFAULT_TTS_API_URL
        self.timeout_seconds = timeout_seconds
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "DUT-AI-Manager/1.0",
        }

    def build_payload(
        self,
        text: str,
        voice: str | None = None,
        model: str | None = None,
        response_format: str | None = None,
        speed: float | None = None,
        stream: bool = False,
        normalize_text: bool | None = None,
        cfg_scale: float | None = None,
        audio_temperature: float | None = None,
        audio_topk: int | None = None,
        audio_topp: float | None = None,
        audio_repetition_penalty: float | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Construct the JSON payload for TTS API request with default parameters."""
        payload: dict[str, Any] = {
            "model": model if model is not None else DEFAULT_MODEL,
            "input": text,
            "voice": voice if voice is not None else DEFAULT_VOICE,
            "response_format": (
                response_format
                if response_format is not None
                else DEFAULT_RESPONSE_FORMAT
            ),
            "speed": speed if speed is not None else DEFAULT_SPEED,
            "stream": stream,
            "normalize_text": (
                normalize_text
                if normalize_text is not None
                else DEFAULT_NORMALIZE_TEXT
            ),
            "cfg_scale": (
                cfg_scale if cfg_scale is not None else DEFAULT_CFG_SCALE
            ),
            "audio_temperature": (
                audio_temperature
                if audio_temperature is not None
                else DEFAULT_AUDIO_TEMPERATURE
            ),
            "audio_topk": (
                audio_topk if audio_topk is not None else DEFAULT_AUDIO_TOPK
            ),
            "audio_topp": (
                audio_topp if audio_topp is not None else DEFAULT_AUDIO_TOPP
            ),
            "audio_repetition_penalty": (
                audio_repetition_penalty
                if audio_repetition_penalty is not None
                else DEFAULT_AUDIO_REPETITION_PENALTY
            ),
        }
        payload.update(kwargs)
        return payload

    def get_mime_type(self, response_format: str | None = None) -> str:
        """Get the MIME content type for a given audio response format."""
        fmt = (response_format or DEFAULT_RESPONSE_FORMAT).lower()
        return self.FORMAT_MIME_MAP.get(fmt, "application/octet-stream")

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        model: str | None = None,
        response_format: str | None = None,
        speed: float | None = None,
        normalize_text: bool | None = None,
        cfg_scale: float | None = None,
        audio_temperature: float | None = None,
        audio_topk: int | None = None,
        audio_topp: float | None = None,
        audio_repetition_penalty: float | None = None,
        **kwargs: Any,
    ) -> bytes:
        """
        Synthesize text into speech audio bytes.

        Args:
            text: Text to be converted into speech
            voice: Voice name (default: 'hamy')
            model: Model identifier (default: 'zerotts')
            response_format: Audio format (default: 'wav')
            speed: Playback speed multiplier (default: 1.0)
            normalize_text: Normalize text before synthesis (default: True)
            cfg_scale: Classifier-free guidance scale (default: 1.0)
            audio_temperature: Temperature for sampling (default: 0.8)
            audio_topk: Top-K cutoff parameter (default: 25)
            audio_topp: Top-P nucleus cutoff parameter (default: 0.95)
            audio_repetition_penalty: Repetition penalty (default: 1.2)

        Returns:
            bytes: The raw audio file bytes.
        """
        if not text or not text.strip():
            raise TTSServiceError("Input text cannot be empty", status_code=400)

        payload = self.build_payload(
            text=text,
            voice=voice,
            model=model,
            response_format=response_format,
            speed=speed,
            stream=False,
            normalize_text=normalize_text,
            cfg_scale=cfg_scale,
            audio_temperature=audio_temperature,
            audio_topk=audio_topk,
            audio_topp=audio_topp,
            audio_repetition_penalty=audio_repetition_penalty,
            **kwargs,
        )

        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        logger.debug(
            f"Calling TTS API at {self.api_url} for voice '{payload.get('voice')}'"
        )

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"TTS API failed status {response.status}: {error_text}"
                        )
                        raise TTSServiceError(
                            f"TTS API failed ({response.status}): {error_text}",
                            status_code=response.status,
                            details=error_text,
                        )

                    audio_data = await response.read()
                    logger.info(
                        f"TTS synthesis done ({len(audio_data)} bytes)"
                    )
                    return audio_data
        except aiohttp.ClientError as exc:
            logger.error(f"Network error during TTS API request: {exc}")
            raise TTSServiceError(
                f"Failed to communicate with TTS service: {exc}",
                status_code=502,
                details=str(exc),
            ) from exc
        except Exception as exc:
            if isinstance(exc, TTSServiceError):
                raise
            logger.exception(f"Unexpected error during TTS synthesis: {exc}")
            raise TTSServiceError(
                f"TTS synthesis failed: {exc}",
                status_code=500,
                details=str(exc),
            ) from exc

    async def synthesize_stream(
        self,
        text: str,
        chunk_size: int = 4096,
        voice: str | None = None,
        model: str | None = None,
        response_format: str | None = None,
        speed: float | None = None,
        normalize_text: bool | None = None,
        cfg_scale: float | None = None,
        audio_temperature: float | None = None,
        audio_topk: int | None = None,
        audio_topp: float | None = None,
        audio_repetition_penalty: float | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """
        Stream synthesized speech audio chunk by chunk.

        Yields:
            bytes: Sequential audio chunks.
        """
        if not text or not text.strip():
            raise TTSServiceError("Input text cannot be empty", status_code=400)

        payload = self.build_payload(
            text=text,
            voice=voice,
            model=model,
            response_format=response_format,
            speed=speed,
            stream=True,
            normalize_text=normalize_text,
            cfg_scale=cfg_scale,
            audio_temperature=audio_temperature,
            audio_topk=audio_topk,
            audio_topp=audio_topp,
            audio_repetition_penalty=audio_repetition_penalty,
            **kwargs,
        )

        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        logger.debug(
            f"Starting streaming TTS for voice '{payload.get('voice')}'"
        )

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"TTS stream failed ({response.status}): {error_text}"
                        )
                        raise TTSServiceError(
                            f"TTS streaming failed ({response.status}): {error_text}",
                            status_code=response.status,
                            details=error_text,
                        )

                    async for chunk in response.content.iter_chunked(chunk_size):
                        yield chunk
        except aiohttp.ClientError as exc:
            logger.error(f"Network error during TTS streaming request: {exc}")
            raise TTSServiceError(
                f"Failed to communicate with TTS streaming service: {exc}",
                status_code=502,
                details=str(exc),
            ) from exc

    async def synthesize_to_file(
        self,
        text: str,
        output_path: str | Path,
        **kwargs: Any,
    ) -> Path:
        """
        Synthesize speech and write directly to a local file.

        Args:
            text: Text to convert to speech
            output_path: Target file path
            **kwargs: Extra arguments passed to `synthesize`

        Returns:
            Path: The resolved output file path
        """
        path = Path(output_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        audio_bytes = await self.synthesize(text, **kwargs)
        path.write_bytes(audio_bytes)
        logger.info(f"Saved TTS audio ({len(audio_bytes)} bytes) to {path}")
        return path

    async def synthesize_and_upload(
        self,
        text: str,
        filename: str | None = None,
        minio_service: Any | None = None,
        prefix: str = "tts",
        **kwargs: Any,
    ) -> str:
        """
        Synthesize speech and immediately upload to S3/MinIO.

        Args:
            text: Text to convert to speech
            filename: Optional custom filename (e.g. 'speech_123.wav')
            minio_service: MinioService instance (optional, instantiates if None)
            prefix: Bucket prefix path
            **kwargs: Extra arguments passed to `synthesize`

        Returns:
            str: The public URL of the uploaded audio file.
        """
        import uuid
        from datetime import datetime

        response_format = kwargs.get("response_format", DEFAULT_RESPONSE_FORMAT)
        ext = f".{response_format.lower()}"

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            filename = f"{prefix}/{timestamp}_{unique_id}{ext}"
        elif not filename.startswith(f"{prefix}/"):
            filename = f"{prefix}/{filename}"

        audio_bytes = await self.synthesize(text, **kwargs)
        content_type = self.get_mime_type(response_format)

        if minio_service is None:
            from app.shared.infrastructure.minio_service import MinioService

            minio_service = MinioService()

        public_url = await minio_service.upload_file(
            file_data=audio_bytes,
            filename=filename,
            content_type=content_type,
        )
        logger.info(f"TTS audio uploaded to MinIO: {public_url}")
        return public_url
