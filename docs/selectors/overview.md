# Selectors — overview

## Problema

Páginas mudam (SPA, BFF, UUID na URL). Um scraper que depende de `a[href="https://…uuid…/login?…"]` quebra. Este projeto descobre um seletor **mais estável** e o devolve em JSON.

## Papéis

| Quem | Faz |
|------|-----|
| `laya_find` | Abre a página, lista candidatos, pergunta ao Laya, devolve `selector` |
| Seu scraper | Navega, preenche, clica, grava — usando o seletor |

## Inputs típicos

- `--url` — página alvo  
- `--intent` — linguagem natural (“campo de senha”, “botão cadastrar agora”)  
- `--mode` — `dom` | `network` | `both`  
- `--policy` — `none` | `light` | `strict`  

## Outputs

Ver [json-contract.md](json-contract.md). Em modo humano (sem `--json`), imprime resumo no terminal.

## Garantias e não-garantias

**Sim:** tentativa de CSS estável; verificação no DOM; cache revalidado; falhas `--json` → `ok:false`.  
**Não:** 100% de acerto do Laya; ausência de redesign; click automático (salvo `--reveal`).

## Próximos docs

- [cli.md](cli.md) · [policies.md](policies.md) · [cache.md](cache.md)  
- Cookbook: [../../examples/LAYA_FIND.md](../../examples/LAYA_FIND.md)
