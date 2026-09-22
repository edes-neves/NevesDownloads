# Neves Downloads

Gerenciador de downloads de vídeos e áudios com interface moderna, suporte a playlists e internacionalização (pt-BR / en-US).

## Funcionalidades

### Download
- Download de vídeos e áudios de diversas plataformas (via yt-dlp)
- Suporte a playlists com seleção individual de vídeos
- Download de playlists completas ou seleção via checkboxes
- Suporte a múltiplas URLs simultâneas (colar várias URLs de uma vez)
- Importação de lista de URLs a partir de arquivo `.txt`
- Detecção automática de URLs em textos colados de plugins de navegador
- Retry automático com backoff exponencial em erros transitórios (rede, rate limit, 5xx)
- Seleção de qualidade: até 4K/2160p, Full HD/1080p, HD/720p, 480p, 360p
- Formatos de vídeo: MP4, WebM
- Formatos de áudio: MP3, M4A, FLAC, OGG, WAV
- Download de legendas com seleção de idiomas
- Embutir thumbnail nos arquivos de áudio
- Organização automática por canal/uploader
- Template personalizado de nomes de arquivo com variáveis (`%(title)s`, `%(ext)s`, `%(uploader)s`, etc.)
- Suporte a cookies de navegador (Chrome, Firefox, Edge, Opera, Vivaldi)
- Suporte a arquivo de cookies `cookies.txt` (export de extensões), com prioridade sobre cookies de navegador — essencial para conteúdo restrito/age-gated
- Playlists de áudio em arquivo único (concatena todos os vídeos em um só MP3/M4A/FLAC/OGG/WAV)
- Otimizações específicas para TikTok (remoção de marca d'água, detecção de tipo de conteúdo)
- Integração com SponsorBlock para remoção automática de segmentos indesejados

### Interface
- Interface moderna com CustomTkinter (temas dark/light/sistema)
- Layout limpo e focado no essencial: URL, tipo, qualidade e modo
- Opções avançadas nas Configurações (cookies, formatos, legendas, organização)
- Cartões de progresso com velocidade, tamanho, ETA e barra de progresso
- Pausar/Retomar download individual e em lote
- Menu completo: Arquivo, Download, Configurações, Editar, Exibir, Histórico, Ajuda
- Navegador de pastas customizado para seleção de destino
- Janela de seleção de vídeos de playlist com checkboxes
- Notificação in-app (toast) ao concluir downloads (vídeo, áudio e lotes)
- Notificação nativa do sistema (notify-send/osascript/PowerShell), desabilitável nas Configurações
- Atalho Ctrl+V para colar URLs

### Internacionalização (i18n)
- Suporte a pt-BR e en-US, configurável nas Configurações
- 287 chaves traduzidas em todos os módulos UI e serviços (com teste de paridade)
- Troca de idioma em tempo real (reinicialização da janela)
- Labels internos mantidos em pt-BR para compatibilidade de configurações

### Configurações
- 31 configurações persistentes organizadas em seções:
  - **Aparência e Idioma**: Tema, idioma (pt-BR/en-US), verificação automática de atualizações
  - **Padrões de Download**: Tipo, modo, qualidade, formato, cookies (navegador ou cookies.txt), organizar, legendas
  - **Rede e Desempenho**: Downloads simultâneos, proxy, limite de velocidade, retries, retries em erros transitórios, timeout
  - **SponsorBlock**: Ativar remoção, categorias configuráveis
  - **TikTok**: Remoção de marca d'água
  - **Nomeação de Arquivos**: Template com variáveis documentadas
  - **Thumbnails**: Embutir, salvar separado
  - **Comportamento**: Confirmação ao sair, auto-limpar concluídos, notificações de conclusão
- Reset para configurações padrão
- Pré-visualização de tema em tempo real

### Gestão de Downloads
- Fila de downloads com limite de concorrência configurável
- Pausar/Retomar individual e em lote
- Fila persistente: pendentes são salvos e retomados no próximo início
- Continuar em segundo plano ao fechar a janela
- Limpeza automática ou manual de concluídos

### Bandeja do sistema
- Ícone na bandeja de notificação (via `pystray`)
- Mostrar/Ocultar, Pausar/Retomar todos, Sair

### Mensagens de erro amigáveis
- Mapeamento automático de erros do yt-dlp para mensagens claras
- Dica de ação sugerida em cada erro

### Histórico
- Histórico persistente (até 500 entradas)
- Exibição formatada: status, tipo, título, uploader, data
- Re-download com um clique (mesmo tipo do registro)

### Auto-update
- Verificação automática de atualizações via GitHub Releases
- Download e instalação de novas versões AppImage
- Notificação ao usuário com opção de atualizar

### Sistema
- Logging com rotação (5 MB, 5 backups) em `~/.neves_downloads/logs/app.log`
- Detecção automática de FFmpeg
- Compatível com desktops Linux (WM_CLASS `nevesdownloads`)
- Suporte a proxy com validação de formato

## Estrutura do Projeto

```
NevesDownloads/
├── main.py                          # Ponto de entrada
├── app/
│   ├── __init__.py                  # Exporta init_language, set_language, _
│   ├── _version.py                  # Fonte única da versão do projeto
│   ├── constants.py                 # Re-export de core/constants.py (compatibilidade)
│   ├── i18n.py                      # Internacionalização (~195 chaves, pt-BR/en-US)
│   ├── core/                        # Domínio da aplicação
│   │   ├── constants.py             # APP_NAME, QUALITY_OPTIONS, etc. (versão vem de _version.py)
│   │   ├── enums.py                 # DownloadStatus, QueueItemStatus, etc. (StrEnum)
│   │   ├── error_patterns.py        # Registry de padrões de erro do yt-dlp
│   │   ├── exceptions.py            # DownloadCancelledError
│   │   ├── settings_schema.py       # SETTINGS_DEFAULTS, validação, tipos
│   │   ├── sponsorblock.py          # DEFAULT_CATEGORIES, SPONSOR_CATEGORY_LABELS
│   │   └── tiktok.py               # TIKTOK_QUALITY_MAP, TIKTOK_CONTENT_I18N
│   ├── models/                      # Dataclasses de dados
│   │   ├── history_entry.py         # HistoryEntry
│   │   ├── queue_item.py            # QueueItem
│   │   ├── download_result.py       # DownloadResult
│   │   ├── error_info.py            # ErrorInfo
│   │   └── tiktok_content_info.py   # TikTokContentInfo
│   ├── services/                    # Lógica de negócio
│   │   ├── settings.py              # Configurações persistentes (JSON)
│   │   ├── history.py               # Histórico de downloads
│   │   ├── queue.py                 # Fila persistente de downloads
│   │   ├── errors.py                # Erros amigáveis (importa core/error_patterns)
│   │   ├── ytdlp_service.py         # Serviço de download via yt-dlp
│   │   ├── updater.py               # Atualização do yt-dlp
│   │   ├── app_updater.py           # Auto-update do app via GitHub Releases
│   │   ├── sponsorblock.py          # Labels de categorias SponsorBlock
│   │   ├── tiktok.py                # Suporte dedicado a TikTok
│   │   ├── tray_manager.py          # Bandeja do sistema (pystray)
│   │   └── clipboard_monitor.py     # Monitor de área de transferência
│   ├── ui/                          # Interface gráfica
│   │   ├── main_window.py           # Janela principal
│   │   ├── download_card.py         # Cartão de progresso
│   │   ├── download_handler.py      # Orquestração de downloads
│   │   ├── settings_window.py       # Janela de configurações
│   │   ├── playlist_window.py       # Seleção de playlists
│   │   ├── folder_browser.py        # Navegador de pastas
│   │   ├── clipboard_handler.py     # Handler de clipboard
│   │   └── tray_handler.py          # Handler da bandeja
│   └── utils/                       # Infraestrutura
│       ├── logger.py                # Logging com rotação (RotatingFileHandler)
│       ├── paths.py                 # Diretórios da aplicação
│       ├── resources.py             # Resolução de assets
│       └── validators.py            # Validação de URLs
├── tests/                           # 339 testes
│   ├── test_i18n.py                 # Testes do módulo i18n
│   ├── test_i18n_smoke.py           # Smoke tests de tradução
│   └── ...                          # Testes unitários e de integração
├── packaging/                       # Scripts de empacotamento
├── assets/                          # Ícone do aplicativo
├── pyproject.toml                   # Configuração do projeto
├── requirements.txt                 # Dependências
├── requirements-dev.txt             # Dependências de desenvolvimento
└── LICENSE                          # Licença MIT
```

## Requisitos

- Python 3.11+
- FFmpeg (recomendado para conversão de formatos, legendas e thumbnails)
- pystray (opcional, para a bandeja do sistema)

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
python main.py
```

## Testes

```bash
./venv/bin/python -m pytest tests/ -x -q
```

## Empacotamento (PyInstaller)

### Linux — AppImage

```bash
./packaging/build_linux.sh --appimage
```

### Windows

```bat
packaging\build_windows.bat
```

### macOS

```bash
./packaging/build_macos.sh --dmg
```

## Auto-update

O app verifica automaticamente novas versões via GitHub Releases.
Ao detectar uma nova versão, o usuário é notificado e pode baixar
o AppImage atualizado diretamente pela interface.

Para publicar uma nova versão:

1. Atualize `__version__` em `app/_version.py` (fonte única — `pyproject.toml`,
   `APP_VERSION` e os scripts de build consultam este arquivo)
2. Crie uma tag Git: `git tag v1.0.0`
3. Push com tag: `git push origin main --tags`
4. O GitHub Actions criará automaticamente a Release com o AppImage

## Desenvolvimento

### Lint e formatação

```bash
./venv/bin/python -m ruff check app/ tests/
./venv/bin/python -m ruff format app/ tests/
```

### Pré-commit hooks

```bash
pre-commit install
```

## Dados do Desenvolvedor

- **Nome**: José Edes Neves
- **Contato**: edes.neves7@gmail.com
- **GitHub**: https://github.com/edes-neves
- **Licença**: MIT
