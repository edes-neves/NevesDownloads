"""
Suporte a internacionalização (i18n).

Fornece a função ``(key)`` que traduz uma chave de string para o idioma
atual configurado nas preferências do aplicativo.  O idioma padrão é
``pt-BR``; ``en-US`` é a segunda opção suportada.

Uso::

    from app.i18n import _

    label = ctk.CTkLabel(frame, text=_("menu.file"))
    dialog_title = _("dialog.update.title")
    msg = _("dialog.update.current_version").format(version=current)
"""

from __future__ import annotations

import logging

logger = logging.getLogger("neves_downloads")

# ── Dicionários de tradução ───────────────────────────────────────

_PT_BR: dict[str, str] = {
    # ── Janela principal ──
    "window.title": "{name} v{version}",
    "subtitle": "Baixe seus vídeos e áudios de forma simples",
    "url_label": "Cole aqui o endereço do vídeo ou playlist (botão direito para colar):",
    # ── Menu Arquivo ──
    "menu.file": "Arquivo",
    "menu.file.paste_url": "Colar URL",
    "menu.file.exit": "Sair",
    # ── Menu Configurações ──
    "menu.settings": "Configurações",
    "menu.settings.title": "Configurações...",
    "menu.settings.folder": "Pasta de destino...",
    # ── Menu Download ──
    "menu.download": "Download",
    "menu.download.pause_all": "Pausar todos",
    "menu.download.resume_all": "Retomar todos",
    "menu.download.background": "Continuar em segundo plano",
    # ── Menu Editar ──
    "menu.edit": "Editar",
    "menu.edit.clear_url": "Limpar campo URL",
    "menu.edit.select_all": "Selecionar todos",
    "menu.edit.clipboard_on": "Ativar monitor de area de transferencia",
    "menu.edit.clipboard_off": "Desativar monitor de area de transferencia",
    # ── Menu Exibir ──
    "menu.view": "Exibir",
    "menu.view.light": "Claro",
    "menu.view.dark": "Escuro",
    "menu.view.system": "Sistema",
    "menu.view.history": "Mostrar historico...",
    # ── Menu Histórico ──
    "menu.history": "Historico",
    "menu.history.view": "Ver historico...",
    "menu.history.clear": "Limpar historico...",
    # ── Menu Ajuda ──
    "menu.help": "Ajuda",
    "menu.help.update_ytdlp": "Verificar atualizacao do yt-dlp...",
    "menu.help.update_app": "Verificar atualização do aplicativo...",
    "menu.help.get_help": "Obter ajuda",
    "menu.help.report_issues": "Relatar problemas...",
    "menu.help.share_ideas": "Compartilhar ideias...",
    "menu.help.about": "Sobre",
    # ── Tipo de download ──
    "type.label": "Tipo:",
    "type.video": "Video",
    "type.audio": "Audio (extrair musica)",
    "quality.label": "Qualidade:",
    "mode.video": "Video unico",
    "mode.playlist_all": "Playlist inteira",
    "mode.playlist_select": "Selecionar videos",
    "subtitles": "Legendas",
    "organize": "Organizar por canal/artista",
    "audio_format": "Formato do audio:",
    "btn.start_download": "INICIAR DOWNLOAD",
    "btn.pause_download": "PAUSAR DOWNLOAD",
    "btn.resume_download": "CONTINUAR DOWNLOAD",
    "btn.cancel_download": "CANCELAR DOWNLOAD",
    "btn.clear_completed": "LIMPAR CONCLUIDOS",
    "downloads_active": "Downloads ativos",
    # ── Menu de contexto ──
    "ctx.paste": "Colar",
    "ctx.clear": "Limpar",
    # ── Sobre ──
    "about.title": "Sobre {name}",
    "about.version": "Versao {version}",
    "about.description": (
        "Gerenciador de downloads de videos e audios\n"
        "com interface moderna e suporte a playlists.\n\n"
        "Suporta centenas de plataformas via yt-dlp,\n"
        "incluindo YouTube, TikTok, Instagram, Facebook,\n"
        "Twitter/X, Vimeo, entre muitas outras.\n\n"
        "Funcionalidades:\n"
        "  - Download de videos e audios (MP3, M4A, FLAC)\n"
        "  - Download de legendas\n"
        "  - Playlists com selecao individual\n"
        "  - Organizacao automatica por canal/artista\n"
        "  - Historico de downloads\n"
        "  - Modo claro, escuro e do sistema"
    ),
    "about.developer": "Desenvolvedor: J. Neves",
    "about.contact": "Contato: nevestecnologias@gmail.com",
    "about.license": (
        "Licenca MIT\n\n"
        "Copyright (c) 2026 J. Neves\n\n"
        "Permissao e concedida, gratuitamente, a qualquer pessoa que obtenha uma\n"
        "copia deste software e dos arquivos de documentacao associados, para lidar\n"
        "com o Software sem restricao, incluindo, sem limitacao, os direitos de usar,\n"
        "copiar, modificar, mesclar, publicar, distribuir, sub-licenciar e/ou vender\n"
        "copias do Software, e permitir que as pessoas a quem o Software seja\n"
        "fornecido o facam, nas seguintes condicoes:\n\n"
        "O aviso de direitos autorais e esta nota de permissao devem ser incluidos em\n"
        "todas as copias ou partes substanciais do Software.\n\n"
        "O SOFTWARE E FORNECIDO 'COMO ESTA', SEM GARANTIA DE QUALQUER TIPO, EXPRESSA\n"
        "OU IMPLICITA, INCLUINDO, MAS NAO SE LIMITANDO A, GARANTIAS DE COMERCIALIZACAO,\n"
        "ADEQUACAO A UM DETERMINADO FIM E NAO VIOLACAO. EM NENHUM CASO OS AUTORES OU\n"
        "TITULARES DOS DIREITOS AUTORAIS SERAO RESPONSAVEIS POR QUALQUER REIVINDICACAO,\n"
        "DANO OU OUTRA RESPONSABILIDADE, SEJA EM ACAO DE CONTRATO, DELITO OU DE OUTRA\n"
        "FORMA, DECORRENTE DE, OU EM CONEXAO COM O SOFTWARE OU O USO OU OUTRAS\n"
        "NEGOCIACOES NO SOFTWARE."
    ),
    "btn.close": "Fechar",
    # ── Atualização do yt-dlp ──
    "dialog.update.title": "Atualização do yt-dlp",
    "dialog.update.check_failed": (
        "Versão atual: {current}\n\n"
        "Não foi possível verificar a versão mais recente.\n"
        "Verifique sua conexão com a internet."
    ),
    "dialog.update.up_to_date": (
        "Versão atual: {current}\nVersão mais recente: {latest}\n\nSeu yt-dlp já está atualizado!"
    ),
    "dialog.update.ask": ("Versão atual: {current}\nVersão mais recente: {latest}\n\nDeseja atualizar agora?"),
    "dialog.update.complete": "{message}\n\nReinicie o Neves Downloads para usar a nova versão.",
    "dialog.update.error_title": "Erro na atualização",
    "dialog.update.error_hint": (
        "{message}\n\nTente atualizar manualmente via terminal:\n  pip install --upgrade yt-dlp"
    ),
    # ── Fechamento ──
    "dialog.exit.title": "Downloads em andamento",
    "dialog.exit.body": (
        "Há {count} download(s) em andamento.\n\n"
        "O que deseja fazer?\n\n"
        "  • Sim  → continuar em segundo plano\n"
        "  • Não  → sair mesmo assim (cancela os downloads)\n"
        "  • Cancelar → voltar ao aplicativo"
    ),
    # ── Contato ──
    "dialog.contact.title": "Contato",
    "dialog.contact.body": "Envie um email para:\n{to}",
    "email.subject.help": "Ajuda - Neves Downloads",
    "email.subject.bug": "Bug Report - Neves Downloads",
    "email.subject.idea": "Sugestao - Neves Downloads",
    # ── Pasta de destino ──
    "folder.select": "Selecionar pasta de destino",
    # ── Configurações ──
    "settings.title": "Configurações",
    "settings.section.appearance": "Aparência e Idioma",
    "settings.appearance_theme": "Tema da interface",
    "settings.language": "Idioma",
    "settings.section.download": "Padrões de Download (pré-seleção ao abrir)",
    "settings.default_type": "Tipo padrão",
    "settings.type.video": "Vídeo",
    "settings.type.audio": "Áudio",
    "settings.default_mode": "Modo padrão",
    "settings.mode.video": "Vídeo único",
    "settings.mode.playlist_all": "Playlist inteira",
    "settings.mode.playlist_select": "Selecionar vídeos",
    "settings.default_quality": "Qualidade padrão",
    "settings.default_format": "Formato de vídeo padrão",
    "settings.default_audio_format": "Formato de áudio padrão",
    "settings.cookies": "Cookies (navegador)",
    "settings.organize": "Organizar downloads por canal/artista (padrão)",
    "settings.download_subtitles": "Baixar legendas (padrão)",
    "settings.subtitle_langs": "Idiomas das legendas (separados por vírgula)",
    "settings.section.network": "Rede e Desempenho",
    "settings.concurrent_downloads": "Downloads simultâneos",
    "settings.proxy": "Proxy (ex: socks5://127.0.0.1:1080)",
    "settings.proxy_placeholder": "Deixe vazio para não usar proxy",
    "settings.speed_limit": "Limite de velocidade (bytes/s, 0 = ilimitado)",
    "settings.retries": "Tentativas (retries)",
    "settings.timeout": "Timeout de rede (segundos)",
    "settings.concurrent_fragments": "Fragments paralelos (multi-threading, 1=desativado)",
    "settings.fragments_hint": "Aumente para downloads mais rápidos em streams HLS/DASH (recomendado: 4-16)",
    "settings.section.sponsorblock": "SponsorBlock (Remoção de Patrocínios)",
    "settings.sponsorblock_enable": "Ativar SponsorBlock (remove segmentos patrocinados em vídeos YouTube)",
    "settings.sponsorblock_categories": "Categorias a remover (separadas por vírgula)",
    "settings.sponsorblock_available": "Disponíveis: {categories}",
    "settings.section.tiktok": "TikTok",
    "settings.tiktok_optimize": "Otimizar downloads do TikTok (melhor qualidade, remover marca d'água)",
    "settings.section.filenames": "Nomeação de Arquivos e Thumbnails",
    "settings.filename_template": "Modelo de nome de arquivo",
    "settings.filename_vars": (
        "Variáveis: %(title)s, %(ext)s, %(uploader)s, %(id)s, %(upload_date)s, %(playlist_title)s, %(playlist_index)s"
    ),
    "settings.embed_thumbnail": "Embutir thumbnail/capa no arquivo (quando possível)",
    "settings.save_thumbnail": "Salvar thumbnail como arquivo separado",
    "settings.section.behavior": "Comportamento",
    "settings.confirm_exit": "Confirmação ao sair com downloads ativos",
    "settings.auto_clear": "Remover automaticamente cartões concluídos",
    "btn.restore_defaults": "Restaurar padrões",
    "btn.save": "Salvar",
    "btn.cancel": "Cancelar",
    "dialog.settings.restore_title": "Restaurar padrões",
    "dialog.settings.restore_body": "Tem certeza que deseja restaurar todas as configurações padrão?",
    "dialog.settings.restored": "Configurações restauradas. Reinicie a janela se desejar.",
    "dialog.settings.saved": "Configurações salvas com sucesso.",
    "dialog.proxy.title": "Proxy",
    "dialog.proxy.body": (
        "Proxy inválido. Use algo como:\n"
        "  http://host:porta\n  https://host:porta\n"
        "  socks5://host:porta\n\nO proxy será ignorado."
    ),
    # ── DownloadCard ──
    "card.preparing": "Preparando...",
    "card.pause": "Pausar",
    "card.resume": "Retomar",
    "card.cancel": "Cancelar",
    "card.cancelling": "Cancelando...",
    "card.completed": "Concluído",
    "card.error": "Erro",
    # ── PlaylistWindow ──
    "playlist.title": "Selecionar vídeos da playlist",
    "playlist.header": "Playlist: {title}",
    "playlist.count": "Total de vídeos: {count}",
    "playlist.videos_label": "Vídeos",
    "playlist.untitled": "Vídeo sem título",
    "playlist.select_all": "Selecionar todos",
    "playlist.deselect_all": "Desmarcar todos",
    "playlist.download_selected": "Baixar selecionados",
    "playlist.cancel": "Cancelar",
    "playlist.none_selected": "Nenhum selecionado",
    "playlist.none_selected_body": "Selecione pelo menos um vídeo para baixar.",
    # ── FolderBrowser ──
    "folder.title": "Selecionar pasta",
    "folder.label": "Pasta:",
    "folder.back": "Voltar",
    "folder.save": "Salvar",
    "folder.cancel": "Cancelar",
    # ── DownloadHandler: validação de URL ──
    "dialog.url_empty": "URL vazia",
    "dialog.url_empty_body": "Por favor, insira uma URL.",
    "dialog.url_invalid": "URL invalida",
    "dialog.url_invalid_body": "Nenhuma URL valida encontrada.\nVerifique se o texto contem URLs http:// ou https://.",
    "dialog.url_invalid_single": "A URL fornecida nao parece ser valida.\nVerifique se comeca com http:// ou https://.",
    "dialog.mode_unsupported": "Modo nao suportado",
    "dialog.mode_unsupported_body": "Selecione uma opcao valida.",
    # ── DownloadHandler: múltiplas URLs ──
    "dialog.batch.title": "Múltiplas URLs detectadas",
    "dialog.batch.body": (
        "Foram detectadas {count} URLs.\n\n"
        "Deseja baixar todas de uma vez?\n\n"
        "  • Sim  → baixa todas em sequência\n"
        "  • Não  → abre a janela de seleção\n"
        "  • Cancelar → mantém o texto como está"
    ),
    "batch.select_title": "Selecionar URLs para download",
    "batch.select_header": "{count} URLs detectadas. Marque as que deseja baixar:",
    "batch.select_all": "Selecionar tudo",
    "batch.cancel": "Cancelar",
    "batch.download_selected": "Baixar selecionados",
    "batch.multiple_urls": "Múltiplas URLs ({count})",
    "batch.selection": "Seleção ({count})",
    # ── DownloadHandler: FFmpeg ──
    "dialog.ffmpeg.title": "FFmpeg nao encontrado",
    "dialog.ffmpeg.body": (
        "FFmpeg nao esta disponivel no sistema.\n"
        "Isso pode causar falhas em downloads de alta qualidade.\n"
        "Deseja continuar mesmo assim?"
    ),
    # ── DownloadHandler: card info ──
    "card.getting_info": "Obtendo informacoes...",
    "card.info_failed": "Falha ao obter informacoes do video.",
    "dialog.playlist_detected": "Playlist detectada",
    "dialog.playlist_detected_body": "Esta URL parece ser uma playlist.\nDeseja abrir a janela de selecao?",
    "card.video_fallback": "Video",
    "card.loading_playlist": "Carregando playlist...",
    "card.playlist_failed": "Nao foi possivel obter a playlist.",
    "card.playlist_empty": "Nenhum video encontrado na playlist.",
    "dialog.error": "Erro",
    "dialog.no_valid_url": "Nenhuma URL valida encontrada.",
    "batch.playlist_title": "Playlist: {title} ({count} videos)",
    "batch.waiting": "{index}. Aguardando...",
    "batch.completed_fallback": "Concluído",
    "batch.progress": "{current}/{total} videos ({ok} ok)",
    "batch.summary": "{success} concluido",
    "batch.summary_errors": "{success}/{total} concluidos, {errors} erro",
    # ── DownloadHandler: fila ──
    "batch.queue_title": "Fila pendente ({count})",
    # ── DownloadHandler: histórico ──
    "dialog.history_empty": "Historico",
    "dialog.history_empty_body": "Nenhum download registrado.",
    "history.title": "Historico de Downloads",
    "history.records": "{count} registros",
    "history.no_title": "Sem titulo",
    "history.status_ok": "OK",
    "history.status_error": "ERRO",
    "history.mode_audio": "Audio",
    "history.mode_video": "Video",
    "btn.fechar": "Fechar",
    "dialog.clear_history": "Limpar Historico",
    "dialog.clear_history_body": "Tem certeza que deseja apagar todo o historico?",
    "dialog.history_cleared": "Historico limpo com sucesso.",
    # ── Erros (friendly_error) ──
    "error.video_privado": "Este vídeo é privado. Você precisa de login ou o link não é público.",
    "error.video_privado_dica": "Tente novamente com cookies de navegador configurados nas Configurações.",
    "error.video_indisponivel": "Este vídeo está indisponível ou foi removido.",
    "error.video_indisponivel_dica": "Verifique se a URL está correta ou se o vídeo ainda existe.",
    "error.regiao_bloqueada": "Este conteúdo não pode ser baixado na sua região (restrição geográfica).",
    "error.regiao_bloqueada_dica": "Use um proxy de outro país nas Configurações.",
    "error.idade_restrita": "Este vídeo possui restrição de idade e requer confirmação de acesso.",
    "error.idade_restrita_dica": "Configure cookies de navegador com uma conta que tenha acesso.",
    "error.login_necessario": "Este download requer autenticação (login).",
    "error.login_necessario_dica": "Configure cookies de navegador nas Configurações e tente novamente.",
    "error.ffmpeg_faltando": "O FFmpeg não está disponível, necessário para este formato/conversão.",
    "error.ffmpeg_faltando_dica": "Instale o FFmpeg no sistema para conversões e legendas.",
    "error.url_invalida": "A URL não é suportada ou não pôde ser reconhecida.",
    "error.url_invalida_dica": "Verifique se a URL é válida e de uma plataforma suportada.",
    "error.timeout": "A conexão excedeu o tempo limite ou não pôde ser estabelecida.",
    "error.timeout_dica": "Verifique sua internet ou aumente o timeout nas Configurações.",
    "error.rate_limit": "Limite de requisições atingido (o site está limitando os downloads).",
    "error.rate_limit_dica": "Aguarde alguns minutos antes de tentar novamente.",
    "error.erro_rede": "Falha de conexão durante o download.",
    "error.erro_rede_dica": "Verifique a conexão com a internet e tente novamente.",
    "error.generico": "Ocorreu um erro inesperado durante o download.",
    "error.generico_dica": "Veja o log do aplicativo para mais detalhes técnicos.",
    # ── TrayManager ──
    "tray.show_hide": "Mostrar/Ocultar janela",
    "tray.pause_all": "Pausar todos",
    "tray.resume_all": "Retomar todos",
    "tray.quit": "Sair",
    # ── TrayHandler ──
    "dialog.background.title": "Em segundo plano",
    "dialog.background.body": (
        "Os downloads continuarão em segundo plano.\n"
        "A janela será minimizada. Para restaurá-la, clique no ícone\n"
        "na barra de tarefas (instale pystray para a bandeja do sistema)."
    ),
    "tray.notification_title": "Neves Downloads em segundo plano",
    "tray.notification_body": "Os downloads continuam ativos na bandeja do sistema.",
    # ── SponsorBlock ──
    "sponsor.sponsor": "Patrocínio",
    "sponsor.selfpromo": "Autopromoção",
    "sponsor.interaction": "Interação (likes, inscrição)",
    "sponsor.intro": "Intro / Abertura",
    "sponsor.outro": "Outro / Final",
    "sponsor.preview": "Preview / Resumo",
    "sponsor.music_official": "Música oficial (copyright)",
    "sponsor.filler": "Preenchimento / Irrelevante",
    # ── TikTok ──
    "tiktok.video": "Vídeo",
    "tiktok.photo": "Foto / Carrossel",
    "tiktok.story": "Story",
    "tiktok.unknown": "Desconhecido",
    "tiktok.tip.video": "TikTok: qualidade máxima ~720p-1080p",
    "tiktok.tip.photo": "TikTok: conteúdo é uma foto/carrossel (será baixado como imagem)",
    "tiktok.tip.story": "TikTok: stories podem expirar. Cookies podem ser necessários.",
    # ── Updater ──
    "updater.unknown_version": "desconhecida",
    "updater.updated": "yt-dlp atualizado de {old} para {new}.",
    "updater.up_to_date": "yt-dlp já está na versão mais recente ({version}).",
    "updater.failed": "Falha ao atualizar yt-dlp: {error}",
    "updater.timeout": "Tempo esgotado ao tentar atualizar yt-dlp (120s).",
    "updater.unexpected_error": "Erro inesperado ao atualizar yt-dlp: {error}",
    "updater.app_updated": "Aplicativo atualizado para a versão {version}. Reinicie para usar.",
    "updater.install_failed": "Falha ao instalar atualização: {error}",
    # ── App updater (GitHub Releases) ──
    "app_updater.checking": "Verificando atualizações...",
    "app_updater.available": "Nova versão disponível: {latest} (atual: {current})",
    "app_updater.up_to_date": "Você está na versão mais recente ({version}).",
    "app_updater.downloading": "Baixando nova versão...",
    "app_updater.downloaded": "Download concluído. Instalando...",
    "app_updater.installed": "Atualização instalada com sucesso!",
    "app_updater.restart_required": "É necessário reiniciar o aplicativo para usar a nova versão.",
    "app_updater.failed": "Falha ao verificar/atualizar o aplicativo: {error}",
    "app_updater.no_asset": "Nenhum binário compatível encontrado na release.",
    "app_updater.ask_update": "Deseja baixar e instalar a versão {version}?",
    # ── Labels de opções (para exibição na UI) ──
    "quality.best": "Melhor disponivel",
    "format.best": "Melhor formato disponivel",
    "cookies.none": "Nenhum",
}

_EN_US: dict[str, str] = {
    # ── Main window ──
    "window.title": "{name} v{version}",
    "subtitle": "Download your videos and audio easily",
    "url_label": "Paste the video or playlist URL here (right-click to paste):",
    # ── File menu ──
    "menu.file": "File",
    "menu.file.paste_url": "Paste URL",
    "menu.file.exit": "Exit",
    # ── Settings menu ──
    "menu.settings": "Settings",
    "menu.settings.title": "Settings...",
    "menu.settings.folder": "Destination folder...",
    # ── Download menu ──
    "menu.download": "Download",
    "menu.download.pause_all": "Pause all",
    "menu.download.resume_all": "Resume all",
    "menu.download.background": "Continue in background",
    # ── Edit menu ──
    "menu.edit": "Edit",
    "menu.edit.clear_url": "Clear URL field",
    "menu.edit.select_all": "Select all",
    "menu.edit.clipboard_on": "Enable clipboard monitor",
    "menu.edit.clipboard_off": "Disable clipboard monitor",
    # ── View menu ──
    "menu.view": "View",
    "menu.view.light": "Light",
    "menu.view.dark": "Dark",
    "menu.view.system": "System",
    "menu.view.history": "Show history...",
    # ── History menu ──
    "menu.history": "History",
    "menu.history.view": "View history...",
    "menu.history.clear": "Clear history...",
    # ── Help menu ──
    "menu.help": "Help",
    "menu.help.update_ytdlp": "Check yt-dlp update...",
    "menu.help.update_app": "Check application update...",
    "menu.help.get_help": "Get help",
    "menu.help.report_issues": "Report issues...",
    "menu.help.share_ideas": "Share ideas...",
    "menu.help.about": "About",
    # ── Download type ──
    "type.label": "Type:",
    "type.video": "Video",
    "type.audio": "Audio (extract music)",
    "quality.label": "Quality:",
    "mode.video": "Single video",
    "mode.playlist_all": "Entire playlist",
    "mode.playlist_select": "Select videos",
    "subtitles": "Subtitles",
    "organize": "Organize by channel/artist",
    "audio_format": "Audio format:",
    "btn.start_download": "START DOWNLOAD",
    "btn.pause_download": "PAUSE DOWNLOAD",
    "btn.resume_download": "RESUME DOWNLOAD",
    "btn.cancel_download": "CANCEL DOWNLOAD",
    "btn.clear_completed": "CLEAR COMPLETED",
    "downloads_active": "Active downloads",
    # ── Context menu ──
    "ctx.paste": "Paste",
    "ctx.clear": "Clear",
    # ── About ──
    "about.title": "About {name}",
    "about.version": "Version {version}",
    "about.description": (
        "Video and audio download manager\n"
        "with modern interface and playlist support.\n\n"
        "Supports hundreds of platforms via yt-dlp,\n"
        "including YouTube, TikTok, Instagram, Facebook,\n"
        "Twitter/X, Vimeo, and many others.\n\n"
        "Features:\n"
        "  - Video and audio downloads (MP3, M4A, FLAC)\n"
        "  - Subtitle downloads\n"
        "  - Playlists with individual selection\n"
        "  - Automatic organization by channel/artist\n"
        "  - Download history\n"
        "  - Light, dark, and system themes"
    ),
    "about.developer": "Developer: J. Neves",
    "about.contact": "Contact: nevestecnologias@gmail.com",
    "about.license": (
        "MIT License\n\n"
        "Copyright (c) 2026 J. Neves\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        "of this software and associated documentation files, to deal in the Software\n"
        "without restriction, including without limitation the rights to use, copy,\n"
        "modify, merge, publish, distribute, sublicense, and/or sell copies of the\n"
        "Software, and to permit persons to whom the Software is furnished to do so,\n"
        "subject to the following conditions:\n\n"
        "The above copyright notice and this permission notice shall be included in all\n"
        "copies or substantial portions of the Software.\n\n"
        "THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
        "SOFTWARE."
    ),
    "btn.close": "Close",
    # ── yt-dlp update dialog ──
    "dialog.update.title": "yt-dlp Update",
    "dialog.update.check_failed": (
        "Current version: {current}\n\nCould not check for the latest version.\nCheck your internet connection."
    ),
    "dialog.update.up_to_date": ("Current version: {current}\nLatest version: {latest}\n\nYour yt-dlp is up to date!"),
    "dialog.update.ask": ("Current version: {current}\nLatest version: {latest}\n\nDo you want to update now?"),
    "dialog.update.complete": "{message}\n\nRestart Neves Downloads to use the new version.",
    "dialog.update.error_title": "Update Error",
    "dialog.update.error_hint": ("{message}\n\nTry updating manually via terminal:\n  pip install --upgrade yt-dlp"),
    # ── Exit dialog ──
    "dialog.exit.title": "Active Downloads",
    "dialog.exit.body": (
        "There are {count} download(s) in progress.\n\n"
        "What would you like to do?\n\n"
        "  • Yes  → continue in background\n"
        "  • No   → exit anyway (cancel downloads)\n"
        "  • Cancel → return to the application"
    ),
    # ── Contact ──
    "dialog.contact.title": "Contact",
    "dialog.contact.body": "Send an email to:\n{to}",
    "email.subject.help": "Help - Neves Downloads",
    "email.subject.bug": "Bug Report - Neves Downloads",
    "email.subject.idea": "Suggestion - Neves Downloads",
    # ── Folder ──
    "folder.select": "Select destination folder",
    # ── Settings ──
    "settings.title": "Settings",
    "settings.section.appearance": "Appearance & Language",
    "settings.appearance_theme": "Interface theme",
    "settings.language": "Language",
    "settings.section.download": "Download Defaults (pre-selection on open)",
    "settings.default_type": "Default type",
    "settings.type.video": "Video",
    "settings.type.audio": "Audio",
    "settings.default_mode": "Default mode",
    "settings.mode.video": "Single video",
    "settings.mode.playlist_all": "Entire playlist",
    "settings.mode.playlist_select": "Select videos",
    "settings.default_quality": "Default quality",
    "settings.default_format": "Default video format",
    "settings.default_audio_format": "Default audio format",
    "settings.cookies": "Cookies (browser)",
    "settings.organize": "Organize downloads by channel/artist (default)",
    "settings.download_subtitles": "Download subtitles (default)",
    "settings.subtitle_langs": "Subtitle languages (comma-separated)",
    "settings.section.network": "Network & Performance",
    "settings.concurrent_downloads": "Concurrent downloads",
    "settings.proxy": "Proxy (e.g. socks5://127.0.0.1:1080)",
    "settings.proxy_placeholder": "Leave empty to disable proxy",
    "settings.speed_limit": "Speed limit (bytes/s, 0 = unlimited)",
    "settings.retries": "Retries",
    "settings.timeout": "Network timeout (seconds)",
    "settings.concurrent_fragments": "Parallel fragments (multi-threading, 1=disabled)",
    "settings.fragments_hint": "Increase for faster HLS/DASH stream downloads (recommended: 4-16)",
    "settings.section.sponsorblock": "SponsorBlock (Sponsor Removal)",
    "settings.sponsorblock_enable": "Enable SponsorBlock (removes sponsored segments in YouTube videos)",
    "settings.sponsorblock_categories": "Categories to remove (comma-separated)",
    "settings.sponsorblock_available": "Available: {categories}",
    "settings.section.tiktok": "TikTok",
    "settings.tiktok_optimize": "Optimize TikTok downloads (better quality, remove watermark)",
    "settings.section.filenames": "File Naming & Thumbnails",
    "settings.filename_template": "Filename template",
    "settings.filename_vars": (
        "Variables: %(title)s, %(ext)s, %(uploader)s, %(id)s, %(upload_date)s, %(playlist_title)s, %(playlist_index)s"
    ),
    "settings.embed_thumbnail": "Embed thumbnail/cover in file (when possible)",
    "settings.save_thumbnail": "Save thumbnail as separate file",
    "settings.section.behavior": "Behavior",
    "settings.confirm_exit": "Confirm on exit with active downloads",
    "settings.auto_clear": "Auto-remove completed cards",
    "btn.restore_defaults": "Restore defaults",
    "btn.save": "Save",
    "btn.cancel": "Cancel",
    "dialog.settings.restore_title": "Restore defaults",
    "dialog.settings.restore_body": "Are you sure you want to restore all default settings?",
    "dialog.settings.restored": "Settings restored. Restart the window if desired.",
    "dialog.settings.saved": "Settings saved successfully.",
    "dialog.proxy.title": "Proxy",
    "dialog.proxy.body": (
        "Invalid proxy. Use something like:\n"
        "  http://host:port\n  https://host:port\n"
        "  socks5://host:port\n\nThe proxy will be ignored."
    ),
    # ── DownloadCard ──
    "card.preparing": "Preparing...",
    "card.pause": "Pause",
    "card.resume": "Resume",
    "card.cancel": "Cancel",
    "card.cancelling": "Cancelling...",
    "card.completed": "Completed",
    "card.error": "Error",
    # ── PlaylistWindow ──
    "playlist.title": "Select playlist videos",
    "playlist.header": "Playlist: {title}",
    "playlist.count": "Total videos: {count}",
    "playlist.videos_label": "Videos",
    "playlist.untitled": "Untitled video",
    "playlist.select_all": "Select all",
    "playlist.deselect_all": "Deselect all",
    "playlist.download_selected": "Download selected",
    "playlist.cancel": "Cancel",
    "playlist.none_selected": "None selected",
    "playlist.none_selected_body": "Please select at least one video to download.",
    # ── FolderBrowser ──
    "folder.title": "Select folder",
    "folder.label": "Folder:",
    "folder.back": "Back",
    "folder.save": "Save",
    "folder.cancel": "Cancel",
    # ── DownloadHandler: URL validation ──
    "dialog.url_empty": "Empty URL",
    "dialog.url_empty_body": "Please enter a URL.",
    "dialog.url_invalid": "Invalid URL",
    "dialog.url_invalid_body": "No valid URL found.\nMake sure the text contains http:// or https:// URLs.",
    "dialog.url_invalid_single": "The provided URL does not seem valid.\nMake sure it starts with http:// or https://.",
    "dialog.mode_unsupported": "Unsupported mode",
    "dialog.mode_unsupported_body": "Please select a valid option.",
    # ── DownloadHandler: multiple URLs ──
    "dialog.batch.title": "Multiple URLs detected",
    "dialog.batch.body": (
        "{count} URLs were detected.\n\n"
        "Do you want to download all of them?\n\n"
        "  • Yes  → download all in sequence\n"
        "  • No   → open the selection window\n"
        "  • Cancel → keep the text as is"
    ),
    "batch.select_title": "Select URLs to download",
    "batch.select_header": "{count} URLs detected. Check the ones you want to download:",
    "batch.select_all": "Select all",
    "batch.cancel": "Cancel",
    "batch.download_selected": "Download selected",
    "batch.multiple_urls": "Multiple URLs ({count})",
    "batch.selection": "Selection ({count})",
    # ── DownloadHandler: FFmpeg ──
    "dialog.ffmpeg.title": "FFmpeg not found",
    "dialog.ffmpeg.body": (
        "FFmpeg is not available on the system.\n"
        "This may cause high-quality downloads to fail.\n"
        "Do you want to continue anyway?"
    ),
    # ── DownloadHandler: card info ──
    "card.getting_info": "Getting info...",
    "card.info_failed": "Failed to get video info.",
    "dialog.playlist_detected": "Playlist detected",
    "dialog.playlist_detected_body": "This URL appears to be a playlist.\nDo you want to open the selection window?",
    "card.video_fallback": "Video",
    "card.loading_playlist": "Loading playlist...",
    "card.playlist_failed": "Could not get the playlist.",
    "card.playlist_empty": "No videos found in the playlist.",
    "dialog.error": "Error",
    "dialog.no_valid_url": "No valid URL found.",
    "batch.playlist_title": "Playlist: {title} ({count} videos)",
    "batch.waiting": "{index}. Waiting...",
    "batch.completed_fallback": "Done",
    "batch.progress": "{current}/{total} videos ({ok} ok)",
    "batch.summary": "{success} completed",
    "batch.summary_errors": "{success}/{total} completed, {errors} error",
    # ── DownloadHandler: queue ──
    "batch.queue_title": "Pending queue ({count})",
    # ── DownloadHandler: history ──
    "dialog.history_empty": "History",
    "dialog.history_empty_body": "No downloads recorded.",
    "history.title": "Download History",
    "history.records": "{count} records",
    "history.no_title": "No title",
    "history.status_ok": "OK",
    "history.status_error": "ERROR",
    "history.mode_audio": "Audio",
    "history.mode_video": "Video",
    "btn.fechar": "Close",
    "dialog.clear_history": "Clear History",
    "dialog.clear_history_body": "Are you sure you want to delete all history?",
    "dialog.history_cleared": "History cleared successfully.",
    # ── Errors (friendly_error) ──
    "error.video_privado": "This video is private. You need to login or the link is not public.",
    "error.video_privado_dica": "Try again with browser cookies configured in Settings.",
    "error.video_indisponivel": "This video is unavailable or has been removed.",
    "error.video_indisponivel_dica": "Check if the URL is correct or if the video still exists.",
    "error.regiao_bloqueada": "This content cannot be downloaded in your region (geo-restriction).",
    "error.regiao_bloqueada_dica": "Use a proxy from another country in Settings.",
    "error.idade_restrita": "This video has an age restriction and requires access confirmation.",
    "error.idade_restrita_dica": "Configure browser cookies with an account that has access.",
    "error.login_necessario": "This download requires authentication (login).",
    "error.login_necessario_dica": "Configure browser cookies in Settings and try again.",
    "error.ffmpeg_faltando": "FFmpeg is not available, required for this format/conversion.",
    "error.ffmpeg_faltando_dica": "Install FFmpeg on the system for conversions and subtitles.",
    "error.url_invalida": "The URL is not supported or could not be recognized.",
    "error.url_invalida_dica": "Check if the URL is valid and from a supported platform.",
    "error.timeout": "The connection timed out or could not be established.",
    "error.timeout_dica": "Check your internet or increase the timeout in Settings.",
    "error.rate_limit": "Rate limit reached (the site is limiting downloads).",
    "error.rate_limit_dica": "Wait a few minutes before trying again.",
    "error.erro_rede": "Connection failure during download.",
    "error.erro_rede_dica": "Check your internet connection and try again.",
    "error.generico": "An unexpected error occurred during download.",
    "error.generico_dica": "See the application log for more technical details.",
    # ── TrayManager ──
    "tray.show_hide": "Show/Hide window",
    "tray.pause_all": "Pause all",
    "tray.resume_all": "Resume all",
    "tray.quit": "Quit",
    # ── TrayHandler ──
    "dialog.background.title": "Background mode",
    "dialog.background.body": (
        "Downloads will continue in the background.\n"
        "The window will be minimized. To restore it, click the icon\n"
        "in the taskbar (install pystray for system tray)."
    ),
    "tray.notification_title": "Neves Downloads in background",
    "tray.notification_body": "Downloads remain active in the system tray.",
    # ── SponsorBlock ──
    "sponsor.sponsor": "Sponsorship",
    "sponsor.selfpromo": "Self-promotion",
    "sponsor.interaction": "Interaction (likes, subscribe)",
    "sponsor.intro": "Intro / Opening",
    "sponsor.outro": "Other / Ending",
    "sponsor.preview": "Preview / Recap",
    "sponsor.music_official": "Official music (copyright)",
    "sponsor.filler": "Filler / Irrelevant",
    # ── TikTok ──
    "tiktok.video": "Video",
    "tiktok.photo": "Photo / Carousel",
    "tiktok.story": "Story",
    "tiktok.unknown": "Unknown",
    "tiktok.tip.video": "TikTok: max quality ~720p-1080p",
    "tiktok.tip.photo": "TikTok: content is a photo/carousel (will be downloaded as image)",
    "tiktok.tip.story": "TikTok: stories may expire. Cookies may be required.",
    # ── Updater ──
    "updater.unknown_version": "unknown",
    "updater.updated": "yt-dlp updated from {old} to {new}.",
    "updater.up_to_date": "yt-dlp is already on the latest version ({version}).",
    "updater.failed": "Failed to update yt-dlp: {error}",
    "updater.timeout": "Timeout while trying to update yt-dlp (120s).",
    "updater.unexpected_error": "Unexpected error updating yt-dlp: {error}",
    "updater.app_updated": "Application updated to version {version}. Please restart to use it.",
    "updater.install_failed": "Failed to install update: {error}",
    # ── App updater (GitHub Releases) ──
    "app_updater.checking": "Checking for updates...",
    "app_updater.available": "New version available: {latest} (current: {current})",
    "app_updater.up_to_date": "You are on the latest version ({version}).",
    "app_updater.downloading": "Downloading new version...",
    "app_updater.downloaded": "Download complete. Installing...",
    "app_updater.installed": "Update installed successfully!",
    "app_updater.restart_required": "Please restart the application to use the new version.",
    "app_updater.failed": "Failed to check/update the application: {error}",
    "app_updater.no_asset": "No compatible binary found in the release.",
    "app_updater.ask_update": "Do you want to download and install version {version}?",
    # ── Option display labels ──
    "quality.best": "Best available",
    "format.best": "Best available format",
    "cookies.none": "None",
}

# ── Idiomas suportados ───────────────────────────────────────────

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "pt-BR": _PT_BR,
    "en-US": _EN_US,
}

_current_language: str = "pt-BR"


def set_language(lang: str) -> None:
    """Define o idioma ativo (``'pt-BR'`` ou ``'en-US'``)."""
    global _current_language
    if lang in _TRANSLATIONS:
        _current_language = lang
    else:
        logger.warning("Idioma desconhecido: %s — usando pt-BR.", lang)
        _current_language = "pt-BR"


def get_language() -> str:
    """Retorna o código do idioma ativo."""
    return _current_language


def _(key: str) -> str:
    """Traduz *key* para o idioma ativo.

    Se a chave não existir no idioma atual, retorna a própria chave
    (fallback seguro para strings em construção).
    """
    table = _TRANSLATIONS.get(_current_language, _PT_BR)
    return table.get(key, _PT_BR.get(key, key))


def init_language() -> None:
    """Lê o idioma salvo nas configurações e aplica."""
    try:
        from app.services import settings

        lang = settings.load("default_language") or "pt-BR"
        set_language(lang)
    except Exception:
        set_language("pt-BR")
