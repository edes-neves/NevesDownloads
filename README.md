# Neves Downloads

Gerenciador de downloads de vídeos e áudios com interface moderna e suporte a playlists.

## Funcionalidades

### Download
- Download de vídeos e áudios de diversas plataformas (via yt-dlp)
- Suporte a playlists com seleção individual de vídeos
- Download de playlists completas ou seleção via checkboxes
- Suporte a múltiplas URLs simultâneas (colar várias URLs de uma vez)
- Detecção automática de URLs em textos colados de plugins de navegador
- Seleção de qualidade: até 4K/2160p, Full HD/1080p, HD/720p, 480p, 360p
- Formatos de vídeo: MP4, WebM
- Formatos de áudio: MP3, M4A, FLAC, OGG, WAV
- Download de legendas com seleção de idiomas
- Embutir thumbnail nos arquivos de áudio
- Organização automática por canal/uploader
- Template personalizado de nomes de arquivo com variáveis (`%(title)s`, `%(ext)s`, `%(uploader)s`, etc.)
- Suporte a cookies de navegador (Chrome, Firefox, Edge, Opera, Brave, Vivaldi, Safari)

### Interface
- Interface moderna com CustomTkinter (temas dark/light/sistema)
- **Layout limpo e focado no essencial**: URL, tipo (Vídeo/Áudio), qualidade e modo
- Opções avançadas (cookies, formatos de vídeo, legendas, organização) nas **Configurações**
- Janela principal com URL multi-linha para colar várias URLs
- Cartões de progresso com velocidade, tamanho, ETA e barra de progresso
- Botão de cancelar download individual
- Botão de pausar/retomar download individual
- Menu completo: Arquivo, Download, Configurações, Editar, Exibir, Histórico, Ajuda
- Menu de contexto (botão direito) na caixa de URL (Colar, Limpar)
- Navegador de pastas customizado para seleção de destino
- Janela de seleção de vídeos de playlist com checkboxes
- Janela de configurações organizada por seções
- Janela "Sobre" com informações do projeto e licença
- Atalho Ctrl+V para colar URLs

### Configurações
- 25 configurações persistentes organizadas em seções:
  - **Aparência e Idioma**: Tema (sistema/claro/escuro), idioma (pt-BR/en-US)
  - **Padrões de Download**: Tipo (vídeo/áudio), modo, qualidade, formato, cookies, organizar por canal, legendas
  - **Rede e Desempenho**: Downloads simultâneos, proxy (HTTP/HTTPS/SOCKS4/SOCKS5), limite de velocidade, retries, timeout
  - **Nomeação de Arquivos**: Template com variáveis documentadas
  - **Thumbnails**: Embutir thumbnail, salvar thumbnail separado
  - **Comportamento**: Confirmação ao sair com downloads ativos, auto-limpar concluídos
- Reset para configurações padrão
- Pré-visualização de tema em tempo real

### Gestão de Downloads
- Fila de downloads com limite de concorrência configurável
- **Pausar/Retomar downloads individualmente** (botão no cartão de progresso)
- **Pausar/Retomar todos** os downloads (menu "Download" e bandeja)
- **Fila persistente**: downloads pendentes são salvos e retomados no próximo início
- Continuar downloads em segundo plano ao fechar a janela
- Confirmação ao sair com downloads ativos
- Limpeza automática ou manual de downloads concluídos
- Botão "Limpar concluídos"

### Bandeja do sistema (tray icon)
- Ícone na bandeja de notificação (via `pystray`)
- Mostrar/Ocultar janela, Pausar/Retomar todos e Sair
- Ao "continuar em segundo plano", a janela é ocultada mas os downloads seguem ativos na bandeja

### Mensagens de erro amigáveis
- Mapeamento automático de erros do `yt-dlp` para mensagens claras em português
  (vídeo privado/indisponível, restrição regional/idade, login, FFmpeg, rede, limite de requisições, etc.)
- Dica de ação sugerida em cada erro

### Histórico
- Histórico persistente de downloads (até 500 entradas)
- Exibição formatada: status, tipo, título, uploader, data
- Limpeza do histórico com confirmação

### Sistema
- Logging em arquivo e console (`~/.neves_downloads/logs/app.log`)
- Detecção automática de FFmpeg
- Detecção de runtimes JavaScript (Deno, Node.js) para yt-dlp
- Compatibilidade com desktops Linux (WM_CLASS `nevesdownloads` definido nativamente via Tk, com reforço via xprop)
- Suporte a proxy com validação de formato

## Requisitos

- Python 3.11+
- FFmpeg (recomendado para conversão de formatos, legendas e thumbnails)
- Deno ou Node.js (opcional, para plugins de extensão de yt-dlp)
- pystray (opcional, para a bandeja do sistema; degrada graciosamente se ausente)

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
python main.py
```

## Empacotamento / Build (PyInstaller)

O projeto empacota em executáveis standalone com PyInstaller. Os scripts se encontram
em `packaging/`.

### Dependências de build

```bash
pip install -r requirements-build.txt   # inclui PyInstaller
```

### Linux — binário e AppImage

`packaging/build_linux.sh` gera um executável único (onefile) e, opcionalmente, um
**AppImage** portátil:

```bash
# binário único (sem AppImage)
./packaging/build_linux.sh

# gera também o AppImage (baixa o appimagetool automaticamente)
./packaging/build_linux.sh --appimage

# modo pasta (onedir) em vez de arquivo único
./packaging/build_linux.sh --onedir
```

Artefatos em `dist/`:
- `NevesDownloads` — executável ELF
- `NevesDownloads-<versão>.AppImage` — AppImage portátil (com `--appimage`)

### Windows — executável .exe

`packaging/build_windows.bat` gera `dist\NevesDownloads.exe` (onefile) e um
`.zip` opcional para distribuição:

```bat
packaging\build_windows.bat
```

### macOS — aplicativo .app

`packaging/build_macos.sh` gera um aplicativo `dist/NevesDownloads.app` e, se o
`create-dmg` estiver instalado, também um instalador `.dmg`:

```bash
./packaging/build_macos.sh          # gera .app
./packaging/build_macos.sh --dmg    # gera também .dmg (precisa de create-dmg)
```

> **Nota:** a extração do ícone no executável é suportada nativamente apenas no
> Windows (`.exe`) e macOS (`.app`). No Linux o ícone é aplicado ao AppImage via
> o arquivo `.desktop`/`.png` no `AppDir`.

## Estrutura do Projeto

```
NevesDownloads/
├── main.py                          # Ponto de entrada
├── app/
│   ├── constants.py                 # Constantes (nome, versão, dev, contato)
│   ├── core/                        # (reservado para lógica de negócio)
│   ├── models/                      # (reservado para modelos de dados)
│   ├── services/
│   │   ├── settings.py              # Sistema de configurações (25 configs, JSON)
│   │   ├── history.py               # Histórico de downloads (JSON, 500 max)
│   │   ├── queue.py                 # Fila persistente de downloads (JSON)
│   │   ├── errors.py                # Mapeamento de erros em mensagens amigáveis
│   │   ├── tray_manager.py          # Bandeja do sistema (pystray)
│   │   └── ytdlp_service.py         # Serviço de download via yt-dlp
│   ├── utils/
│   │   ├── logger.py                # Configuração de logging
│   │   ├── paths.py                 # Gerenciamento de diretórios
│   │   ├── resources.py             # Resolução de assets (dev e empacotado)
│   │   └── validators.py            # Validação de URLs
│   └── ui/
│       ├── main_window.py           # Janela principal
│       ├── download_card.py         # Cartão de progresso de download
│       ├── folder_browser.py        # Navegador de pastas customizado
│       ├── playlist_window.py       # Janela de seleção de playlists
│       └── settings_window.py       # Janela de configurações
├── assets/
│   └── Icone.png                    # Ícone do aplicativo
├── packaging/                       # Scripts/arquivos de empacotamento
│   ├── NevesDownloads.spec          # Especificação do PyInstaller
│   ├── build_linux.sh               # Build Linux (binário + AppImage)
│   ├── build_windows.bat            # Build Windows (.exe)
│   ├── build_macos.sh               # Build macOS (.app / .dmg)
│   └── requirements-build.txt       # Dependências de build (PyInstaller)
├── data/logs/                       # Diretório de logs
├── requirements.txt                 # Dependências
└── LICENSE                          # Licença MIT
```

## Dados do Desenvolvedor

- **Nome**: José Edes Neves
- **Contato**: edes.neves7@gmail.com
- **Licença**: MIT
