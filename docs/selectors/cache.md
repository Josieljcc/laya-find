# Cache de seletores

Implementação: `examples/laya_find_lib/cache.py`.

## Comportamento

- **Arquivo:** `examples/selector_cache.json` (gitignored)  
- **Chave:** `host[:port]::intent` normalizado  
- **Hit:** revalida seletor na página; se OK → `"cached": true` e pula torneio  
- **Miss / stale:** rediscover e grava só seletor DOM **estável** e verificado  
- **Network:** cache DOM **não** atende `--mode network` / kind network  

## Flags

```text
--use-cache          # padrão
--no-cache           # não lê nem grava
--cache-path PATH    # outro arquivo
```

## Invalidação

1. `--no-cache` numa run  
2. Apagar chave ou o arquivo JSON  
3. Redesign do site → seletor falha na revalidação e a entrada some sozinha  

## Cuidado

Mesmo host + mesmo intent em páginas diferentes pode reutilizar CTA do header (desejável para marketing; atrapalha se as páginas forem muito distintas).
