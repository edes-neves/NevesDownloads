"""
Serviço de edição de mídia: corte de um trecho de vídeo/áudio com FFmpeg.

O corte é feito após o download, diretamente no arquivo salvo. A lógica é
pura (sem dependência de Tk), permitindo teste unitário completo.

Estratégia: tenta primeiro um corte com remux rápido (-c copy, sem perda de
qualidade); se o FFmpeg falhar (ex.: fluxos que não podem ser copiados),
re-encoda com codecs compatíveis com o container de saída (webm → VP9/Opus,
mp3 → LBAME, etc.), evitando erros de muxing.
"""

from __future__ import annotations

import logging
import re
import subprocess
import threading
from pathlib import Path

from app.services.ytdlp_service import _locate_ffmpeg

logger = logging.getLogger("neves_downloads")

_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d{2}):(\d{2}(?:\.\d+)?)")
_CUT_SUFFIX = "_cortado"
_AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac", ".wma"}


def _is_audio_file(path: Path | str) -> bool:
    return Path(path).suffix.lower() in _AUDIO_EXTS


def parse_timestamp(text: str) -> float:
    """Converte 'HH:MM:SS', 'MM:SS' ou segundos em valor float (segundos).

    Exemplos: '1:02:03' -> 3723.0; '02:03' -> 123.0; '45' -> 45.0.
    Lança ValueError se o texto não for um tempo válido.
    """
    raw = (text or "").strip()
    if not raw:
        raise ValueError("tempo vazio")
    parts = raw.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        if len(parts) == 1:
            return float(parts[0])
    except ValueError:
        pass
    raise ValueError(f"tempo inválido: {raw!r}")


def format_timestamp(seconds: float) -> str:
    """Formata segundos como 'HH:MM:SS.mmm' para uso direto no FFmpeg."""
    seconds = max(0.0, float(seconds))
    hours = int(seconds // 3600)
    minutes = int(seconds % 3600 // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def parse_duration_from_ffmpeg(ffmpeg_stderr: str) -> float | None:
    """Extrai a duração do vídeo da saída padrão do FFmpeg (-i entrada)."""
    match = _DURATION_RE.search(ffmpeg_stderr or "")
    if not match:
        return None
    hours, minutes, seconds = int(match.group(1)), int(match.group(2)), float(match.group(3))
    return hours * 3600 + minutes * 60 + seconds


def get_media_duration(path: Path | str, ffmpeg_location: str | None = None) -> float | None:
    """Retorna a duração do arquivo em segundos (None se indisponível)."""
    ffmpeg = ffmpeg_location or _locate_ffmpeg()
    if not ffmpeg:
        return None
    try:
        proc = subprocess.run(
            [ffmpeg, "-hide_banner", "-i", str(path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_duration_from_ffmpeg(proc.stderr)


def _reencode_args(output_path: Path | str, input_is_audio: bool) -> list[str]:
    """Argumentos de re-encode compatíveis com o container de saída.

    Previne erros de muxing do FFmpeg: H.264/AAC não podem ser gravados em
    WebM (usa VP9/Opus), e AAC não pode ser multiplexado em MP3 (usa LAME).
    """
    suffix = Path(output_path).suffix.lower()
    if input_is_audio:
        if suffix == ".mp3":
            return ["-c:a", "libmp3lame", "-b:a", "192k"]
        if suffix in {".m4a", ".aac"}:
            return ["-c:a", "aac", "-b:a", "192k"]
        if suffix in {".opus", ".ogg"}:
            return ["-c:a", "libopus", "-b:a", "160k"]
        if suffix == ".flac":
            return ["-c:a", "flac"]
        if suffix == ".wav":
            return ["-c:a", "pcm_s16le"]
        return ["-c:a", "aac", "-b:a", "192k"]
    if suffix == ".webm":
        return ["-c:v", "libvpx-vp9", "-crf", "34", "-b:v", "0", "-c:a", "libopus"]
    args = ["-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac"]
    if suffix in {".mp4", ".mov", ".m4v"}:
        args += ["-movflags", "+faststart"]
    return args


def build_cut_command(
    ffmpeg: str,
    input_path: Path | str,
    output_path: Path | str,
    start: float,
    end: float | None,
    strategy: str = "copy",
) -> list[str]:
    """Monta a linha de comando do FFmpeg para o corte de *start* a *end*."""
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-y",
        "-ss",
        format_timestamp(start),
        "-i",
        str(input_path),
    ]
    if end is not None:
        cmd += ["-to", format_timestamp(end)]
    if strategy == "copy":
        # Remux rápido: copia os fluxos sem perder qualidade.
        cmd += ["-c", "copy", "-map_metadata", "0", "-avoid_negative_ts", "make_zero"]
    elif _is_audio_file(input_path):
        # Arquivo só de áudio: re-encoda apenas o áudio, conforme o container.
        cmd += _reencode_args(output_path, input_is_audio=True)
    else:
        # Re-encoda para cortar em ponto arbitrário quando a cópia falha.
        cmd += _reencode_args(output_path, input_is_audio=False)
    cmd.append(str(output_path))
    return cmd


def make_cut_output(input_path: Path | str, suffix: str = _CUT_SUFFIX) -> Path:
    """Gera o caminho de saída: '<nome>_cortado.<ext>', evitando sobrescrever."""
    source = Path(input_path)
    candidate = source.with_name(source.stem + suffix + source.suffix)
    counter = 2
    while candidate.exists():
        candidate = source.with_name(f"{source.stem}{suffix}({counter}){source.suffix}")
        counter += 1
    return candidate


def _run_ffmpeg(cmd: list[str], cancel_event: threading.Event | None) -> tuple[int, str]:
    """Executa o FFmpeg, respeitando cancelamento. Retorna (código, stderr)."""
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except (OSError, subprocess.SubprocessError) as exc:
        return -1, str(exc)
    while True:
        try:
            proc.wait(timeout=0.2)
            break
        except subprocess.TimeoutExpired:
            if cancel_event is not None and cancel_event.is_set():
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                return -1, "cancelled"
    _, stderr = proc.communicate()
    return proc.returncode, (stderr or "")[-2000:]


def cut_media(
    input_path: Path | str,
    output_path: Path | str,
    start: float,
    end: float | None = None,
    ffmpeg_location: str | None = None,
    cancel_event: threading.Event | None = None,
) -> dict:
    """Corta o trecho [start, end) do arquivo, salvando em output_path.

    end None significa 'até o final do arquivo'. Retorna um dict com
    'status' ('completed' | 'error' | 'cancelled') e detalhes.
    """
    ffmpeg = ffmpeg_location or _locate_ffmpeg()
    if not ffmpeg:
        return {
            "status": "error",
            "error": (
                "ffmpeg não encontrado ou não executável. Instale o FFmpeg no sistema "
                "(ex.: `sudo apt install ffmpeg`, `sudo pacman -S ffmpeg`, `winget install ffmpeg`)."
            ),
        }

    source = Path(input_path)
    if not source.is_file():
        return {"status": "error", "error": "arquivo de entrada não encontrado"}

    duration = get_media_duration(source, ffmpeg_location=ffmpeg)
    start = float(start)
    end_value = float(end) if end is not None else duration

    if start < 0:
        return {"status": "error", "error": "início negativo"}
    if end_value is not None and end_value <= start:
        return {"status": "error", "error": "fim deve ser maior que o início"}
    if duration is not None:
        if start >= duration:
            return {"status": "error", "error": "início além da duração"}
        if end_value is not None and end_value > duration:
            end_value = duration

    last_error = ""
    for strategy in ("copy", "reencode"):
        cmd = build_cut_command(ffmpeg, source, output_path, start, end_value, strategy)
        logger.info("Corte (FFmpeg %s): %s", strategy, cmd)
        returncode, stderr = _run_ffmpeg(cmd, cancel_event)
        result_path = Path(output_path)
        if returncode == -1:
            return {"status": "cancelled", "error": "cancelado"}
        if returncode == 0 and result_path.is_file() and result_path.stat().st_size > 0:
            cut_duration = None
            if end_value is not None:
                cut_duration = round(end_value - start, 3)
            logger.info("Corte concluído: %s", result_path)
            return {"status": "completed", "output": str(result_path), "duration": cut_duration}
        last_error = stderr or f"código {returncode}"

    return {"status": "error", "error": last_error}
