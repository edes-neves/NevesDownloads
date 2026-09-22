import logging
import os
import shutil
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp

from app.core.exceptions import DownloadCancelledError

logger = logging.getLogger("neves_downloads")


def _find_js_runtimes() -> dict[str, Any]:
    """
    Detecta runtimes JavaScript disponíveis no sistema e retorna
    no formato esperado pelo yt-dlp (dict de {runtime: {config}}).
    """
    runtimes = {}
    # Procura deno em locais comuns
    deno_path = shutil.which("deno")
    if not deno_path:
        deno_home = os.path.expanduser("~/.deno/bin/deno")
        if os.path.isfile(deno_home) and os.access(deno_home, os.X_OK):
            deno_path = deno_home
    if deno_path:
        runtimes["deno"] = {"path": deno_path}
    # Procura node
    node_path = shutil.which("node")
    if node_path:
        runtimes["node"] = {"path": node_path}
    return runtimes


def _get_impersonate_target():
    """
    Retorna um alvo de impersonação de navegador suportado pelo yt-dlp
    (exige o pacote curl_cffi). None se indisponível.
    """
    try:
        from yt_dlp.networking._curlcffi import CurlCFFIRH
    except Exception:
        return None
    for target in getattr(CurlCFFIRH, "supported_targets", None) or ():
        if getattr(target, "client", None) == "chrome":
            return target
    return None


_IMPERSONATE_TARGET = _get_impersonate_target()


def _needs_impersonation(url: str) -> bool:
    """Facebook bloqueia a extração sem fingerprint de navegador; exige impersonação."""
    host = (url or "").lower()
    return "facebook.com" in host or "fbcdn.net" in host


class YtDlpService:
    """Serviço para interagir com yt-dlp."""

    def __init__(self):
        self._js_runtimes = _find_js_runtimes()
        if self._js_runtimes:
            logger.info(f"Runtimes JS encontrados: {list(self._js_runtimes.keys())}")
        else:
            logger.warning("Nenhum runtime JavaScript encontrado. Instale deno ou node para melhor compatibilidade.")
        # Cache do status do FFmpeg
        self._ffmpeg_available = None
        # Opções base compartilhadas para reutilização
        self._base_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 3,
        }
        if self._js_runtimes:
            self._base_opts["js_runtimes"] = self._js_runtimes

    def is_ffmpeg_available(self) -> bool:
        """Verifica se o FFmpeg está disponível no sistema (com cache)."""
        if self._ffmpeg_available is None:
            self._ffmpeg_available = shutil.which("ffmpeg") is not None
            if self._ffmpeg_available:
                logger.info("FFmpeg encontrado no sistema.")
            else:
                logger.warning("FFmpeg não encontrado. Alguns downloads podem falhar.")
        return self._ffmpeg_available

    def _build_base_opts(
        self,
        cookies_browser: str | None = None,
        proxy: str | None = None,
        retries: int | None = None,
        socket_timeout: int | None = None,
        url: str | None = None,
    ) -> dict[str, Any]:
        """Retorna opções base compartilhadas, adicionando cookies/proxy se fornecido."""
        opts = dict(self._base_opts)
        if retries is not None:
            opts["retries"] = retries
            opts["fragment_retries"] = retries
        if socket_timeout is not None:
            opts["socket_timeout"] = socket_timeout
        if proxy:
            opts["proxy"] = proxy
        if cookies_browser:
            opts["cookiesfrombrowser"] = (cookies_browser,)
        # Facebook exige fingerprint de navegador; usa impersonação se disponível
        if url and _needs_impersonation(url) and _IMPERSONATE_TARGET is not None:
            opts["impersonate"] = _IMPERSONATE_TARGET
        return opts

    def extract_info(
        self,
        url: str,
        cookies_browser: str | None = None,
    ) -> dict[str, Any] | None:
        try:
            opts = self._build_base_opts(cookies_browser, url=url)
            opts["extract_flat"] = False
            opts["noplaylist"] = True
            with yt_dlp.YoutubeDL(opts) as ydl:
                info: dict[str, Any] | None = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            logger.error(f"Erro ao extrair informações de {url}: {e}")
            return None

    def extract_playlist_info(
        self,
        url: str,
        cookies_browser: str | None = None,
        playlistend: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Extrai informações da playlist usando extract_flat=True.
        Retorna apenas metadados básicos (título, URL, duração) sem
        resolver cada vídeo individualmente, o que é muito mais rápido.
        """
        opts = self._build_base_opts(cookies_browser, url=url)
        opts["extract_flat"] = True
        opts["ignoreerrors"] = True
        if playlistend:
            opts["playlistend"] = playlistend
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info: dict[str, Any] | None = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            logger.error(f"Erro ao extrair playlist de {url}: {e}")
            return None

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Remove caracteres inválidos de nomes de arquivo/pasta."""
        invalids = '<>:"/\\|?*'
        for ch in invalids:
            name = name.replace(ch, "_")
        return name.strip().strip(".")

    @staticmethod
    def _cleanup_partial_files(output_path: Path) -> None:
        """Remove arquivos parciais (.part) deixados pelo yt-dlp ao cancelar."""
        if not output_path.exists():
            return
        for f in output_path.iterdir():
            if f.is_file() and f.suffix == ".part":
                try:
                    f.unlink()
                    logger.info("Arquivo parcial removido: %s", f.name)
                except OSError as e:
                    logger.warning("Falha ao remover %s: %s", f.name, e)

    def _resolve_output_path(
        self,
        output_path: Path,
        info: dict[str, Any],
        organize: bool,
    ) -> Path:
        """Se organize=True, cria subpasta por canal. Retorna path final."""
        if not organize:
            return output_path
        channel = info.get("uploader") or info.get("channel") or info.get("creator") or ""
        if channel:
            folder = output_path / self._sanitize_filename(channel)
            folder.mkdir(parents=True, exist_ok=True)
            return folder
        return output_path

    def download_video(
        self,
        url: str,
        output_path: Path,
        quality: str = "Melhor disponível",
        fmt: str = "MP4",
        mode: str = "video",
        audio_fmt: str = "MP3",
        subtitles: bool = False,
        subtitle_langs: str = "pt,en",
        organize: bool = False,
        progress_hook: Callable | None = None,
        cancel_event: threading.Event | None = None,
        pause_event: threading.Event | None = None,
        cookies_browser: str | None = None,
        proxy: str | None = None,
        retries: int | None = None,
        socket_timeout: int | None = None,
        filename_template: str | None = None,
        embed_thumbnail: bool = False,
        write_thumbnail: bool = False,
        limit_speed: int = 0,
        sponsorblock_enabled: bool = False,
        sponsorblock_categories: str | None = None,
        concurrent_fragments: int = 1,
        tiktok_watermark_removal: bool = False,
    ) -> dict[str, Any]:
        quality_map = {
            # A sintaxe `bestvideo*+bestaudio/best` baixa vídeo e áudio em
            # unidades separadas (DASH) e as mescla via FFmpeg. O sufixo
            # "/best" cobre vídeos que só oferecem formatos progressivos
            # (já combinados). Sem isso, vídeos do YouTube que só possuem
            # trilhas DASH separadas falham com "Requested format is not
            # available".
            "Melhor disponivel": "bestvideo*+bestaudio/best",
            "4K / 2160p": "bestvideo*[height<=2160]+bestaudio/best[height<=2160]/best",
            "2K / 1440p": "bestvideo*[height<=1440]+bestaudio/best[height<=1440]/best",
            "Full HD / 1080p": "bestvideo*[height<=1080]+bestaudio/best[height<=1080]/best",
            "HD / 720p": "bestvideo*[height<=720]+bestaudio/best[height<=720]/best",
            "480p": "bestvideo*[height<=480]+bestaudio/best[height<=480]/best",
            "360p": "bestvideo*[height<=360]+bestaudio/best[height<=360]/best",
        }
        format_selector = quality_map.get(quality) or quality_map.get("Melhor disponivel")

        ext_map = {
            "MP4": "mp4",
            "WebM": "webm",
            "Melhor formato disponível": "mp4",
        }
        ext = ext_map.get(fmt) or ext_map.get("Melhor formato disponivel", "mp4")

        # Se for WebM, forçar formato WebM (vídeo e áudio em webm)
        if fmt == "WebM":
            format_selector = "bestvideo*[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best"

        ydl_opts = self._build_base_opts(
            cookies_browser,
            proxy=proxy,
            retries=retries,
            socket_timeout=socket_timeout,
            url=url,
        )

        # Template de nome de arquivo
        outtmpl = filename_template or "%(title)s.%(ext)s"

        # Limite de velocidade (ratelimit)
        if limit_speed and limit_speed > 0:
            ydl_opts["ratelimit"] = limit_speed

        # ── Multi-threading: fragments paralelos (HLS/DASH) ──
        if concurrent_fragments and concurrent_fragments > 1:
            ydl_opts["concurrent_fragment_downloads"] = concurrent_fragments

        # ── SponsorBlock: remoção de segmentos ──
        if sponsorblock_enabled:
            cats = sponsorblock_categories or "sponsor,selfpromo,interaction,intro,outro,preview"
            cat_list = [c.strip() for c in cats.split(",") if c.strip()]
            if cat_list:
                ydl_opts["sponsorblock_remove"] = cat_list

        # ── TikTok: otimizações específicas ──
        from app.services.tiktok import is_tiktok_url

        is_tiktok = is_tiktok_url(url)
        if is_tiktok:
            # TikTok: qualidade máxima ~1080p, forçar melhor disponível
            if quality in ("4K / 2160p", "2K / 1440p"):
                format_selector = "bestvideo*[height<=1080]+bestaudio/best[height<=1080]/best"
            # Remoção de marca d'água: usar formato com melhor qualidade
            if tiktok_watermark_removal:
                # O yt-dlp com --no-check-certificates consegue melhor qualidade
                ydl_opts["http_headers"] = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36",
                }

        # ── Modo áudio ──
        if mode == "audio":
            audio_map = {
                "MP3": ("mp3", "mp3"),
                "M4A": ("m4a", "m4a"),
                "FLAC": ("flac", "flac"),
                "OGG": ("ogg", "ogg"),
                "WAV": ("wav", "wav"),
            }
            _audio_ext, postprocessor_ext = audio_map.get(audio_fmt, ("mp3", "mp3"))
            ydl_opts.update(
                {
                    "outtmpl": str(output_path / outtmpl),
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": postprocessor_ext,
                            "preferredquality": "0",
                        }
                    ],
                    "noplaylist": True,
                }
            )
            if not self.is_ffmpeg_available():
                ydl_opts["format"] = "best[ext=m4a]/best[ext=mp3]/best"
                ydl_opts.pop("postprocessors", None)
        else:
            ydl_opts.update(
                {
                    "outtmpl": str(output_path / outtmpl),
                    "format": format_selector,
                    "merge_output_format": ext,
                    "noplaylist": True,
                }
            )
            if not self.is_ffmpeg_available():
                # Sem FFmpeg não dá para mesclar vídeo+áudio separados,
                # então limita a formatos progressivos (já combinados).
                ydl_opts["format"] = "best[ext=mp4]/best"

        # ── Legendas ──
        if subtitles and mode != "audio":
            langs = [lang.strip() for lang in subtitle_langs.split(",") if lang.strip()]
            ydl_opts.update(
                {
                    "writesubtitles": True,
                    "writeautomaticsub": True,
                    "subtitleslangs": langs if langs else ["pt", "en"],
                    "subtitlesformat": "srt/best",
                    "postprocessors": [
                        *ydl_opts.get("postprocessors", []),
                        {
                            "key": "FFmpegSubtitlesConvertor",
                            "format": "srt",
                        },
                    ],
                }
            )

        # ── Thumbnail (capa) ──
        if embed_thumbnail or write_thumbnail:
            ydl_opts["writethumbnail"] = True
            pp = ydl_opts.get("postprocessors", [])
            if embed_thumbnail:
                pp = [*pp, {"key": "EmbedThumbnail"}]
            if mode == "audio":
                pp = [
                    *pp,
                    {
                        "key": "FFmpegMetadata",
                        "add_metadata": True,
                    },
                ]
            ydl_opts["postprocessors"] = pp

        # Hook de cancelamento & pausa
        hooks = []
        if progress_hook:
            hooks.append(progress_hook)

        if cancel_event:

            def _cancel_hook(d):
                if cancel_event.is_set():
                    raise DownloadCancelledError("Download cancelado pelo usuário")

            hooks.append(_cancel_hook)

        if pause_event is not None:

            def _pause_hook(d):
                # Bloqueia/aguarda enquanto o download estiver pausado
                while pause_event.is_set():
                    if cancel_event is not None and cancel_event.is_set():
                        raise DownloadCancelledError("Download cancelado durante pausa")
                    # Sleep real: sem travamento de CPU (Event.wait volta imediato
                    # quando o evento já está setado, gerando busy-wait)
                    time.sleep(0.3)

            hooks.append(_pause_hook)

        ydl_opts["progress_hooks"] = hooks

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    return {
                        "status": "error",
                        "error": "Não foi possível obter informações do vídeo.",
                    }

                # Resolve organização por canal
                final_path = self._resolve_output_path(output_path, info, organize)

                filename = ydl.prepare_filename(info)
                # Para áudio, o yt-dlp pode trocar a extensão
                if mode == "audio" and self.is_ffmpeg_available():
                    base = Path(filename).stem
                    audio_ext_final = audio_map.get(audio_fmt, ("mp3",))[0]
                    filename = str(final_path / f"{base}.{audio_ext_final}")
                else:
                    filename = str(final_path / Path(filename).name)

                # Move o arquivo para a subpasta do canal (se necessário)
                if organize and final_path != output_path:
                    src = Path(ydl.prepare_filename(info))
                    if src.exists() and str(src) != filename:
                        shutil.move(str(src), filename)

                return {
                    "status": "completed",
                    "filename": filename,
                    "title": info.get("title", ""),
                    "uploader": info.get("uploader", info.get("channel", "")),
                    "filesize": info.get("filesize", 0),
                }
        except DownloadCancelledError:
            logger.info(f"Download cancelado: {url}")
            self._cleanup_partial_files(output_path)
            return {
                "status": "cancelled",
                "error": "Cancelado pelo usuário.",
            }
        except Exception as e:
            logger.error(f"Erro no download: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    # ── Playlist (múltiplos vídeos) ─────────────────────────────
    # O download é sequencial; cada vídeo passa pelo mesmo fluxo da
    # download_video (formato, legendas, thumbnail, cancelamento/pausa).
    def download_playlist(
        self,
        urls: list[str],
        output_path: Path,
        quality: str = "Melhor disponível",
        fmt: str = "MP4",
        mode: str = "video",
        audio_fmt: str = "MP3",
        subtitles: bool = False,
        subtitle_langs: str = "pt,en",
        organize: bool = False,
        progress_callback: Callable | None = None,
        video_progress_callback: Callable | None = None,
        cancel_event: threading.Event | None = None,
        pause_event: threading.Event | None = None,
        cookies_browser: str | None = None,
        proxy: str | None = None,
        retries: int | None = None,
        socket_timeout: int | None = None,
        filename_template: str | None = None,
        embed_thumbnail: bool = False,
        write_thumbnail: bool = False,
        limit_speed: int = 0,
        sponsorblock_enabled: bool = False,
        sponsorblock_categories: str | None = None,
        concurrent_fragments: int = 1,
        tiktok_watermark_removal: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Baixa uma lista de URLs (vídeos) sequencialmente.
        Retorna lista de resultados para cada vídeo.
        """
        results = []
        total = len(urls)
        for idx, url in enumerate(urls):
            if cancel_event and cancel_event.is_set():
                break

            # Aguarda se pausado (entre vídeos de uma playlist)
            if pause_event is not None:
                while pause_event.is_set():
                    if cancel_event and cancel_event.is_set():
                        break
                    time.sleep(0.3)
            if cancel_event and cancel_event.is_set():
                break

            # Notifica progresso geral
            if progress_callback:
                progress_callback({"current": idx + 1, "total": total, "status": "downloading", "url": url})

            # Baixa vídeo individual
            result = self.download_video(
                url=url,
                output_path=output_path,
                quality=quality,
                fmt=fmt,
                mode=mode,
                audio_fmt=audio_fmt,
                subtitles=subtitles,
                subtitle_langs=subtitle_langs,
                organize=organize,
                progress_hook=video_progress_callback,
                cancel_event=cancel_event,
                pause_event=pause_event,
                cookies_browser=cookies_browser,
                proxy=proxy,
                retries=retries,
                socket_timeout=socket_timeout,
                filename_template=filename_template,
                embed_thumbnail=embed_thumbnail,
                write_thumbnail=write_thumbnail,
                limit_speed=limit_speed,
                sponsorblock_enabled=sponsorblock_enabled,
                sponsorblock_categories=sponsorblock_categories,
                concurrent_fragments=concurrent_fragments,
                tiktok_watermark_removal=tiktok_watermark_removal,
            )
            results.append(result)

            if progress_callback:
                progress_callback(
                    {
                        "current": idx + 1,
                        "total": total,
                        "status": "completed" if result.get("status") == "completed" else "error",
                        "url": url,
                        "result": result,
                    }
                )

        return results
