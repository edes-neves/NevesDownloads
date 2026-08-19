# Neves Downloads

Gerenciador de downloads de vídeos e áudios com interface moderna e suporte a playlists.

## Funcionalidades

### Download
- Download de vídeos e áudios de diversas plataformas (via yt-dlp)
- Suporte a playlists com seleção individual de vídeos
- Download de playlists completas ou seleção via checkboxes
- Suporte a múltiplas URLs simultâneas (colar várias URLs de uma vez)
- Detecção automática de URLs em textos colados de plugins de navegador
- Seleção de qualidade: até 4K/2160p, Full HD/1080p, HD/720p, 480p, 360p, 240p
- Formatos de vídeo: MP4, WebM
- Formatos de áudio: MP3, M4A, FLAC, OGG, WAV
- Download de legendas com seleção de idiomas
- Embutir thumbnail nos arquivos de áudio
- Organização automática por canal/uploader
- Template personalizado de nomes de arquivo com variáveis (`%(title)s`, `%(ext)s`, `%(uploader)s`, etc.)
- Suporte a cookies de navegador (Chrome, Firefox, Edge, Opera, Brave, Vivaldi, Safari)

### Interface
- Interface moderna com CustomTkinter (temas dark/light/sistema)
- Janela principal com URL multi-linha para colar várias URLs
- Cartões de progresso com velocidade, tamanho, ETA e barra de progresso
- Botão de cancelar download individual
- Menu completo: Arquivo, Configurações, Editar, Exibir, Histórico, Ajuda
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
- Continuar downloads em segundo plano ao fechar a janela
- Confirmação ao sair com downloads ativos
- Limpeza automática ou manual de downloads concluídos
- Botão "Limpar concluídos"

### Histórico
- Histórico persistente de downloads (até 500 entradas)
- Exibição formatada: status, tipo, título, uploader, data
- Limpeza do histórico com confirmação

### Sistema
- Logging em arquivo e console (`~/.neves_downloads/logs/app.log`)
- Detecção automática de FFmpeg
- Detecção de runtimes JavaScript (Deno, Node.js) para yt-dlp
- Compatibilidade com desktops Linux (WM_CLASS via xdotool/xprop)
- Suporte a proxy com validação de formato

## Requisitos

- Python 3.12+
- FFmpeg (recomendado para conversão de formatos, legendas e thumbnails)
- Deno ou Node.js (opcional, para plugins de extensão de yt-dlp)

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
python main.py
```

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
│   │   └── ytdlp_service.py         # Serviço de download via yt-dlp
│   ├── utils/
│   │   ├── logger.py                # Configuração de logging
│   │   ├── paths.py                 # Gerenciamento de diretórios
│   │   └── validators.py            # Validação de URLs
│   └── ui/
│       ├── main_window.py           # Janela principal
│       ├── download_card.py         # Cartão de progresso de download
│       ├── folder_browser.py        # Navegador de pastas customizado
│       ├── playlist_window.py       # Janela de seleção de playlists
│       └── settings_window.py       # Janela de configurações
├── assets/
│   └── Icone.png                    # Ícone do aplicativo
├── data/logs/                       # Diretório de logs
├── requirements.txt                 # Dependências
└── LICENSE                          # Licença MIT
```

## Dados do Desenvolvedor

- **Nome**: José Edes Neves
- **Contato**: edes.neves7@gmail.com
- **Licença**: MIT
