# Padrões e referências TypeScript

## Modelagem por situação

| Situação | Escolha |
| --- | --- |
| Estado finito com campos que variam por caso | Union discriminada com campo `kind`/`status`/`type` literal |
| Conjunto fechado e conhecido de chaves | `Record<K, V>` ou mapped type sobre uma union de literais |
| Dado vindo de fora (rede, arquivo, env) | Schema runtime (`zod`, `valibot` ou equivalente) que produz o tipo validado |
| API pública que outro pacote pode estender (`declare module`, merge) | `interface` |
| Tipo interno, union, tupla ou tipo computado | `type` alias |
| Invariante que sempre deve valer (ex.: string não vazia, range) | Constructor/factory function que só devolve o tipo se a invariante for provada, nunca um cast |

## `strict` e narrowing

- `strictNullChecks` é o efeito mais valioso do modo strict: sem ele,
  `null`/`undefined` passam por qualquer tipo silenciosamente.
- `noUncheckedIndexedAccess` adiciona `| undefined` a todo acesso por índice
  (`arr[i]`, `record[key]`) — ative quando o projeto tolera o esforço de
  narrowing adicional; ele pega bugs reais de índice fora do range.
- Narrowing por `typeof`, `instanceof`, campo discriminante ou type guard
  (`function isX(v: unknown): v is X`) é preferível a `as` em qualquer
  situação em que o valor pode ser inspecionado em runtime.
- `unknown` é o tipo de entrada correto para dado não confiável; `any`
  desliga a checagem de tipo para todo o resto da cadeia a partir dali —
  usar `any` é equivalente a sair do TypeScript naquele ponto.

## `satisfies` vs anotação vs inferência

| Objetivo | Ferramenta |
| --- | --- |
| Deixar o compilador inferir o tipo mais preciso possível de um valor interno | Nenhuma anotação — deixe a inferência trabalhar |
| Checar que um valor cumpre um tipo, mas preservar o tipo literal mais específico inferido (ex.: chaves de um objeto de rotas, paleta de tokens) | `satisfies T` |
| Fixar o tipo de uma API pública para que ela não mude de forma silenciosa quando a implementação mudar | Anotação explícita de retorno na assinatura exportada |
| Alargar deliberadamente um literal para o tipo base (ex.: permitir novas chaves depois) | Anotação explícita (`const x: T = {...}`), que descarta o tipo literal |

`const config = {...} satisfies Record<string, Route>` mantém `config.home`
com o tipo literal da rota específica (autocomplete e narrowing exatos),
enquanto `const config: Record<string, Route> = {...}` alarga todo acesso
para o tipo genérico `Route`. Use `satisfies` sempre que o consumidor do
valor se beneficia do tipo mais específico e o papel do tipo declarado é só
validar, não substituir, a inferência.

## Generics

- Um parâmetro de tipo só se justifica quando relaciona duas ou mais partes
  da assinatura (parâmetro de entrada e tipo de retorno, chave e valor).
  Sem essa relação, o generic é ruído.
- Prefira `T extends unknown` implícito a `T extends any` em constraints;
  constraints amplas demais (`T extends object`) raramente pegam erro real.
- Funções de ordem superior devem inferir o generic do argumento passado
  (`function map<T, U>(arr: T[], fn: (x: T) => U): U[]`), nunca exigir que o
  chamador declare o tipo manualmente quando a inferência já resolve.

## Módulos

- Use `import type { X }` para importar apenas tipos — permite que o
  bundler elimine o import na saída JS e evita ciclo de import desnecessário
  em runtime.
- Confirme `"type": "module"` ou `"commonjs"` no `package.json` e a extensão
  de import (`.js` explícito em ESM Node) antes de assumir que uma
  biblioteca resolve igual em todos os targets.
- Bibliotecas que suportam ESM e CJS devem declarar `exports` com
  condições (`import`/`require`/`types`) coerentes; um `types` apontando para
  o arquivo errado quebra apenas para quem consome via um dos dois formatos.

## Bibliotecas e API pública

- Toda função exportada tem assinatura anotada explicitamente (parâmetros e
  retorno); depender de inferência numa API pública trava a forma exposta ao
  primeiro uso e dificulta mudança controlada depois.
- Gere e revise as declarations (`.d.ts`) publicadas — um erro de
  `tsconfig` (`declaration`, `declarationMap`) pode publicar tipo incorreto
  mesmo com o build passando.
- Mudança de tipo público que quebra um consumidor existente é mudança
  major em SemVer, mesmo que nenhuma linha de runtime tenha mudado.

## Validação runtime nas fronteiras

- Tipo estático desaparece em runtime; um payload de API, arquivo de config
  ou variável de ambiente deve ser validado por um schema que produza o tipo
  (parse, não apenas cast) antes de ser tratado como confiável.
- Erros de validação devem ser diferenciáveis de erros de lógica de negócio
  — trate-os como uma categoria própria de falha (dado malformado), com
  mensagem que aponta o campo e o valor recebido.

## Fontes oficiais

- Handbook: https://www.typescriptlang.org/docs/handbook/intro.html
- Narrowing: https://www.typescriptlang.org/docs/handbook/2/narrowing.html
- Generics: https://www.typescriptlang.org/docs/handbook/2/generics.html
- Modules: https://www.typescriptlang.org/docs/handbook/modules.html
- TSConfig reference: https://www.typescriptlang.org/tsconfig/
- Declaration files: https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html
- Do's and Don'ts: https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html
- Semantic Versioning: https://semver.org/
