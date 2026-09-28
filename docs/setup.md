# Setup

Instalação passo a passo em **Linux**, **macOS** e **Windows**. Depois do venv ativo, os comandos (`laya-find`, `laya-login`, `laya-serve`, `pytest`) são os mesmos em todos os sistemas.

## Requisitos

| Item | Detalhe |
|------|---------|
| Python | **3.12** recomendado; mínimo **3.10** |
| Git | Para clonar o repositório |
| Rede | 1ª descarga de checkpoints Hugging Face (cache local depois) |
| Display | `laya-login` e `--headed` precisam de GUI (Chromium headed) |

No Linux, o Playwright pode pedir libs do sistema na primeira instalação do Chromium — o próprio `playwright install` indica o que falta (`playwright install-deps chromium` se necessário).

## 1. Clonar e entrar no repo

```bash
git clone https://github.com/Josieljcc/laya-find.git
cd laya-find
```

## 2. Criar o ambiente virtual

**Linux / macOS**

```bash
python3.12 -m venv .venv
# se python3.12 não existir: python3 -m venv .venv  (confira: python3 --version ≥ 3.10)
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Com o venv ativo, `python` e `pip` apontam para `.venv`. Sem ativar, use os caminhos diretos:

| OS | Python | CLIs |
|----|--------|------|
| Linux / macOS | `.venv/bin/python` | `.venv/bin/laya-find` |
| Windows | `.venv\Scripts\python.exe` | `.venv\Scripts\laya-find.exe` |

## 3. Instalar o pacote e o Chromium

Com o venv **ativo** (qualquer OS):

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

Isso instala `laya-find`, `laya-login`, `laya-serve` e as deps de desenvolvimento.

## 4. Verificar

```bash
laya-find --help
laya-login --help
python -m laya_find --help
python -m pytest tests -q
```

## 5. Subir o `laya-serve`

Em um **segundo** terminal, ative o mesmo venv e:

**Linux / macOS**

```bash
export LAYA_HOST=127.0.0.1
export LAYA_PORT=8000
export LAYA_PRELOAD=1
export LAYA_MODELS=multilingual   # ou english,multilingual
export LAYA_DEVICE=cpu            # cuda/xpu se disponível
laya-serve
```

**Windows (PowerShell)**

```powershell
$env:LAYA_HOST='127.0.0.1'
$env:LAYA_PORT='8000'
$env:LAYA_PRELOAD='1'
$env:LAYA_MODELS='multilingual'
$env:LAYA_DEVICE='cpu'
laya-serve
```

Health check:

```bash
curl -s http://127.0.0.1:8000/health
```

Variáveis úteis (upstream Laya): `LAYA_API_KEY`, `LAYA_THREADS`, `HF_TOKEN` (rate limit Hub).

Se a porta 8000 já estiver em uso, use o processo existente ou mude `LAYA_PORT`.

## 6. Primeiro find

Com `laya-serve` no ar:

```bash
laya-find --policy strict \
  --url "https://exemplo.com/" \
  --mode dom \
  --intent "botão de login" \
  --json --settle-ms 3000
```

Página atrás de login (manual na janela do browser):

```bash
laya-login --login-url "https://exemplo.com/login"
```

Stdout = uma linha JSON; logs = stderr. Contrato: [selectors/json-contract.md](selectors/json-contract.md).

## Notas por plataforma

### Encoding no Windows

Se caracteres especiais saírem quebrados no console:

```powershell
$env:PYTHONIOENCODING='utf-8'
```

### Linux headless / CI

`laya-find` sem `--headed` roda Chromium headless. `laya-login` exige display (X11/Wayland ou sessões remotas com GUI). Em CI, use só find headless + `laya-serve`.

### macOS

Python via [python.org](https://www.python.org/downloads/), Homebrew (`brew install python@3.12`) ou pyenv. O resto é igual ao Linux (`source .venv/bin/activate`).

## Próximo passo

- Integração scraper: [../examples/LAYA_FIND.md](../examples/LAYA_FIND.md)  
- Arquitetura: [architecture.md](architecture.md)  
- Agentes: [../AGENTS.md](../AGENTS.md)
