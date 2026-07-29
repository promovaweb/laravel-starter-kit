---
name: specsfy-specialist-react-ui-components
description: Escolher, compor e adaptar uma biblioteca de componentes React com Tailwind CSS para landing pages, marketing, navegação, formulários, dados, feedback e tipografia. Use quando uma interface React precisar de referências TSX reutilizáveis, exemplos visuais ou uma composição de página; use sempre em conjunto com a skill specsfy-specialist-ui-design, que governa hierarquia, layout, estados e coerência visual.
---

# Componentes React de interface

## Quando usar

- Acionar quando uma interface React precisar ser criada a partir dos 231
  exemplos TSX versionados em `assets/components/`.
- Acionar para comparar variantes de navegação, formulário, dados, feedback,
  marketing ou tipografia sem introduzir uma biblioteca de runtime.
- Não acionar para corrigir estado, effects ou concorrência sem trabalho visual;
  usar `$specsfy-specialist-react`.
- Usar sempre com `$specsfy-specialist-ui-design`, que decide hierarquia,
  composição e densidade antes da escolha do asset.

## Fluxo

1. Anunciar o uso conjunto e carregar `$specsfy-specialist-ui-design` antes de
   escolher uma referência.
2. Inspecionar versão do React, framework, Tailwind, design system, componentes
   locais, ícones e estratégia de testes do projeto consumidor.
3. Definir com a skill de UI a tarefa principal, hierarquia, composição,
   densidade, estados e breakpoints.
4. Escolher a família em [references/catalog.md](references/catalog.md) e listar
   somente os assets candidatos em `assets/components/<familia>/`.
5. Ler a menor quantidade de arquivos TSX capaz de comparar variantes.
6. Adaptar a referência aos tokens, componentes, rotas, dados e convenções
   observados; não substituir a arquitetura local pela estrutura do exemplo.
7. Implementar todos os estados relevantes e validar comportamento, aparência,
   responsividade e acessibilidade.

Para páginas completas, ler
[references/composition-map.md](references/composition-map.md). Para conduzir
uma escolha incremental, ler
[references/conversation-flow.md](references/conversation-flow.md).

## Padrões

- Tratar os arquivos em `assets/` como referências copiáveis, nunca como pacote
  ou dependência de runtime.
- Preservar semântica, teclado, foco, `aria-*`, `sr-only`, `alt`, dark mode e
  breakpoints úteis ao adaptar.
- Preferir tokens, primitives, `Link`, imagens e componentes já publicados no
  projeto consumidor.
- Substituir dados mockados, URLs externas, `href="#"` e copy de demonstração.
- Confirmar dependências explícitas do asset, como Headless UI ou Heroicons,
  antes de usá-las; não instalar pacotes sem autorização.
- Manter a composição definida por `$specsfy-specialist-ui-design`; a
  disponibilidade de um exemplo não justifica adicionar uma seção.
- Combinar com `$specsfy-specialist-react` para ownership de estado, effects,
  concorrência ou testes React e com
  `$specsfy-specialist-web-accessibility` para auditoria aprofundada.

## Antipadrões

- Copiar uma página inteira e manter dados mockados, imports inexistentes ou
  links `#`; o exemplo deixa de ser referência e vira dívida acoplada.
- Escolher um asset pela aparência antes de definir tarefa e hierarquia; isso
  faz o catálogo dirigir o produto em vez de servir à intenção da tela.
- Instalar todas as dependências citadas por um exemplo sem inventariar os
  primitives locais; cria duas fontes concorrentes de componentes e tokens.
- Transformar componentes estáticos em Client Components por conveniência;
  aumenta JavaScript enviado e mistura apresentação com estado sem necessidade.

## Validação

- Executar os testes, lint e typecheck já definidos pelo projeto consumidor.
- Exercitar estados nominal, loading, empty, error, disabled e permission denied
  quando forem relevantes.
- Verificar mobile e desktop, zoom, overflow, conteúdo curto/longo, teclado,
  foco, contraste e reduced motion.
- Confirmar que imports e assets externos existem e que nenhum pacote foi
  introduzido implicitamente.
- Revisar a interface final com
  [references/interface-quality-checklist.md](references/interface-quality-checklist.md)
  e com `$specsfy-specialist-ui-design`.
- Não declarar a interface integrada sem demonstrar interação por teclado,
  estados adversos e ausência de overflow nos breakpoints suportados.

## Skills relacionadas

- `$specsfy-specialist-shadcn-ui` fornece primitives adaptáveis; esta skill
  fornece composições TSX copiáveis, não uma dependência runtime.
- `$specsfy-specialist-ui-design` governa composição, hierarquia, densidade e
  coerência visual; esta skill fornece material React adaptável.
- `$specsfy-specialist-react` governa ownership de estado, effects, concorrência
  e testes de comportamento.
- `$specsfy-specialist-tailwind-css` governa tokens e utilitários usados na
  adaptação visual.
- `$specsfy-specialist-web-accessibility` conduz auditoria WCAG e testes com
  tecnologia assistiva além da checagem básica da interface.
- `$specsfy-specialist-nextjs` ou `$specsfy-specialist-astro` governa a
  fronteira server/client e o roteamento do framework hospedeiro.

Leia [references/standards.md](references/standards.md) para critérios de
seleção, adaptação, estado, dependências e evidência, e carregue os demais
arquivos de `references/` somente no passo do Fluxo que os solicita.
