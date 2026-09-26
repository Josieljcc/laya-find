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
| `src/laya_find/cli.py` | CLI Typer e entry point `laya-find` |
| `src/laya_find/find.py` | Orquestra coleta, política, torneio, cache e JSON |
| `src/laya_find/` | Módulos de produto testáveis |
| `examples/` | Demos que consomem a CLI; não contém a implementação |
| Cache JSON | Acelera revisitas; revalida seletor antes de hit |
| Scraper do usuário | Ação real na página |

## Módulos (`src/laya_find`)

| Módulo | Papel |
|--------|-------|
| `cli.py` | Flags Typer, validação e códigos de saída |
| `find.py` | Pipeline Playwright → Laya → resultado |
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
