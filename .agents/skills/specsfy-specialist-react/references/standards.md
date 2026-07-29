# Padrões e referências React

## Onde o estado deve morar

| Situação | Onde colocar |
| --- | --- |
| Só um componente lê e escreve | `useState` local nesse componente |
| Dois componentes irmãos precisam do mesmo valor | Elevar ao ancestral comum mais próximo, não ao topo da árvore |
| Muitos componentes distantes leem, poucos escrevem | `useReducer` + `Context` isolado por responsabilidade |
| Dado pertence ao servidor (lista, registro, sessão) | Biblioteca de data fetching (cache, revalidação) — não duplicar em `useState` |
| Transição com múltiplos eventos relacionados | `useReducer`, uma máquina de estados explícita em vez de vários booleanos |

Regra geral: comece pelo estado mais local possível e suba apenas quando dois
consumidores realmente divergem sem ele. Descer estado depois é sempre mais
barato que desacoplar um god-context depois.

## Effects: quando usar e quando não

`useEffect` sincroniza um componente com um sistema **fora** do React (DOM,
subscription de terceiros, WebSocket, `localStorage`, timers, medição de
layout). Não é para:

- Computar um valor a partir de props/state já disponíveis — calcule direto
  no corpo do componente, ou use `useMemo` se o cálculo for caro.
- Resetar estado quando uma prop muda — troque a `key` do componente para
  remontá-lo, em vez de um effect que chama `setState`.
- Encadear um `setState` que dispara outro effect — geralmente é um evento de
  usuário, não uma sincronização; mova a lógica para o handler.
- Buscar dados sem cancelamento: todo fetch em effect precisa checar se o
  componente ainda está montado ou usar `AbortController`, senão uma resposta
  atrasada de uma requisição obsoleta sobrescreve o estado mais recente
  ("race condition" clássica de fetch-in-effect).

## Listas e identidade

- `key` vem do dado (id estável), nunca do índice do array quando itens podem
  ser inseridos, removidos ou reordenados — índice como key faz o React
  reconciliar o elemento errado e vaza estado local entre itens diferentes.
- Evite gerar a key no render (`key={Math.random()}` ou `key={crypto.randomUUID()}`
  a cada render) — isso força remount total a cada atualização.

## Context

- Um `Context.Provider` deve cobrir a menor árvore que realmente precisa do
  valor. Um único context "global" com todo o estado da aplicação
  rerenderiza qualquer consumidor a cada mudança de qualquer campo.
- Separe contexts por frequência de mudança: um valor que muda a cada tecla
  (ex.: texto de busca) não deve estar no mesmo provider que preferências
  raramente alteradas (ex.: tema).
- Para estado compartilhado com atualizações de alta frequência e muitos
  consumidores, considere uma biblioteca de estado externa com seletor
  granular em vez de `Context` puro.

## Concorrência e Suspense

- `useTransition`/`startTransition` marca uma atualização como não urgente
  (ex.: filtrar uma lista grande) sem bloquear a interação em andamento
  (digitação, clique).
- `Suspense` e error boundaries devem envolver apenas o boundary que sabe se
  recuperar (mostrar fallback, tentar de novo) — não a aplicação inteira, ou
  qualquer suspensão profunda derruba toda a UI.

## Memoização

- `memo`, `useMemo` e `useCallback` têm custo de comparação e de memória; cada
  um só compensa quando: (a) o cálculo/render evitado é comprovadamente caro,
  ou (b) a referência estável evita um re-render em cascata medido, ou (c) é
  exigido por uma dependência de outro hook. Meça (profiler, contagem de
  renders) antes de aplicar — memoização especulativa piora legibilidade sem
  ganho.

## Testes

- Teste pela experiência de quem usa: texto visível, papel ARIA, valor de
  input, foco — nunca por nome de hook interno ou estrutura de componente.
- Cubra todos os estados modelados (nominal, loading, empty, error, stale,
  optimistic) e o caminho de recuperação de erro, não só o caminho feliz.
- Trate warnings do React no console como falha de teste, não ruído — eles
  geralmente indicam key ausente, hook fora de ordem ou `setState` após
  unmount.

## Fontes oficiais

- React: https://react.dev/
- Pensando em React: https://react.dev/learn/thinking-in-react
- Managing State: https://react.dev/learn/managing-state
- You Might Not Need an Effect: https://react.dev/learn/you-might-not-need-an-effect
- Synchronizing with Effects: https://react.dev/learn/synchronizing-with-effects
- Escape Hatches: https://react.dev/learn/escape-hatches
- startTransition: https://react.dev/reference/react/startTransition
- Profiler: https://react.dev/reference/react/Profiler
- Testing Library guiding principles: https://testing-library.com/docs/guiding-principles/
- WAI-ARIA APG: https://www.w3.org/WAI/ARIA/apg/
