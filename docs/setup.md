# Setup

## Requisitos

- Windows PowerShell (comandos abaixo) ou shell equivalente  
- Python **3.12** recomendado (`py -3.12`); mínimo 3.10  
- Git opcional (este workspace pode não ter remote)  
- Rede na 1ª descarga de checkpoints Hugging Face  

## Ambiente virtual

```powershell
cd C:\laya
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install "laya[serve]" playwright pytest
.\.venv\Scripts\python.exe -m playwright install chromium
```

Verificar:

```powershell
.\.venv\Scripts\python.exe -I -c "import laya; print(laya.__version__)"
.\.venv\Scripts\python.exe -m pytest tests -q
```

## `laya-serve`

Em um terminal dedicado:

```powershell
cd C:\laya
$env:LAYA_HOST='127.0.0.1'
$env:LAYA_PORT='8000'
$env:LAYA_PRELOAD='1'
$env:LAYA_MODELS='multilingual'   # ou english,multilingual
$env:LAYA_DEVICE='cpu'            # cuda/xpu se disponível
.\.venv\Scripts\laya-serve.exe
```

Health:

```powershell
curl.exe -s http://127.0.0.1:8000/health
```

Variáveis úteis (upstream Laya): `LAYA_API_KEY`, `LAYA_THREADS`, `HF_TOKEN` (rate limit Hub).

Se a porta 8000 já estiver em uso (`WinError 10048`), use o processo existente ou mude `LAYA_PORT`.

## Encoding no Windows

```powershell
$env:PYTHONIOENCODING='utf-8'
```

## Próximo passo

- Humanos / integração: [../examples/LAYA_FIND.md](../examples/LAYA_FIND.md)  
- Arquitetura: [architecture.md](architecture.md)  
- Agentes: [../AGENTS.md](../AGENTS.md)
