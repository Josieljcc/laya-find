# Políticas (`--policy`)

Implementação: `examples/laya_find_lib/policy.py`.

| Valor | Comportamento | Uso |
|-------|---------------|-----|
| **`light`** (padrão) | Dedupe + soft-rank por tokens do intent | Default seguro |
| **`strict`** | Narrow agressivo (senha→password, frase “cadastrar agora”, etc.) + rank | Sites barulhentos / intent claro |
| **`none`** | Só dedupe; torneio embaralhado | Depuração; Laya “nu” (mais erro) |

`laya_find_heuristic.py` força `strict`.

## Dicas

- Intent claro (“campo de senha”) → `strict` costuma acertar mais.  
- Se `strict` eliminar o certo demais → tente `light`.  
- Se heurística empurrar o errado → `none` (aceite flakiness) ou refine o intent.  
- Coleta sempre pode incluir `button`+`link` quando o kind é button (CTA estilizado como `<a>`).

Mais contexto: [../../examples/LAYA_FIND.md](../../examples/LAYA_FIND.md).
