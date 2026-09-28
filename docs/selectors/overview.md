# Selectors — overview

## Problema

Páginas mudam (SPA, BFF, UUID na URL). Um scraper que depende de `a[href="https://…uuid…/login?…"]` quebra. Este projeto descobre um seletor **mais estável** e o devolve em JSON.

## Papéis

| Quem | Faz |
|------|-----|
| `laya-find` | Abre a página, lista candidatos, pergunta ao Laya, devolve `selector` |
| `laya-login` | Login **manual** headed; depois roda find na **mesma** sessão Playwright |
| Seu scraper | Navega, preenche, clica, grava — usando o seletor |

## Inputs típicos

- `--url` — página alvo  
- `--intent` — linguagem natural (“campo de senha”, “botão cadastrar agora”, “cabeçalho collapse”, “imagem do módulo”)  
- `--mode` — `dom` | `network` | `both`  
- `--policy` — `none` | `light` | `strict`  
- `--kind` — opcional: `input` | `button` | `link` | `select` | `clickable` | `image` | `network`  

`clickable` = div/span clicável (cursor-pointer, collapse, etc.), não `button`/`a` nativos.  
`image` = `<img>` (thumbs/capas); prefira intents que excluam logos se houver vários.

## Outputs

Ver [json-contract.md](json-contract.md). Em modo humano (sem `--json`), imprime resumo no terminal.

Instale com `pip install -e ".[dev]"` e execute por `laya-find` / `laya-login` ou `python -m laya_find`. A implementação fica em `src/laya_find/`; `examples/` contém somente demos de consumo.

## Garantias e não-garantias

**Sim:** tentativa de CSS estável; verificação no DOM; cache revalidado; falhas `--json` → `ok:false`.  
**Não:** 100% de acerto do Laya; ausência de redesign; fill/click automático de credenciais (salvo `--reveal` no find).

## Próximos docs

- [cli.md](cli.md) · [policies.md](policies.md) · [cache.md](cache.md)  
- Cookbook: [../../examples/LAYA_FIND.md](../../examples/LAYA_FIND.md)
