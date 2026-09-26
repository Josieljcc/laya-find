# Arquitetura

## Visão

```
URL + intent
    → Playwright (DOM e/ou network)
    → candidatos (+ dedupe por destino)
    → política (none|light|strict)
    → torneio Laya (lotes) + noul opcional
    → seletor estável verificado
    → JSON / stdout  →  scraper externo
```

`laya-serve` é o backend de decisão. O find **não** substitui o scraper.

## Componentes

| Componente | Responsabilidade |
|------------|------------------|
| `laya-serve` | Inferência tipada HTTP |
| `examples/laya_find.py` | CLI: coleta, política, torneio, cache, JSON |
| `examples/laya_find_lib/` | Lógica testável (sem browser nos unit tests) |
| Cache JSON | Acelera revisitas; revalida seletor antes de hit |
| Scraper do usuário | Ação real na página |

## Módulos (`laya_find_lib`)

| Módulo | Papel |
|--------|-------|
| `selectors.py` | Volatilidade / candidatos `href*=` estáveis |
| `normalize.py` | Destino canônico (strip UUID/query) + dedupe |
| `policy.py` | `apply_policy` none/light/strict |
| `decide.py` | Labels curtas + overlap para retry |
| `cache.py` | Persistência host+intent → seletor |
| `contract.py` | `build_result` / `emit_json_line` |

## Fluxo de confiança

1. Coleta ampla o suficiente (button inclui links CTA).  
2. Remove clones do mesmo destino.  
3. Política reduz / ordena candidatos.  
4. Laya escolhe em lotes; se confiança baixa, um retry com overlap de intent.  
5. `repair_selector` prefere CSS estável; `verify_selector` confere no DOM vivo.  
6. Cache só grava seletor DOM estável e verificado.

## O que não entra aqui

- Cadeias fill → click → assert (seu scraper).  
- Treinar/fine-tune Laya (upstream / notebooks oficiais).  

Detalhes de CLI: [selectors/cli.md](selectors/cli.md) · Políticas: [selectors/policies.md](selectors/policies.md)
