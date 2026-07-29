---
name: specsfy-specialist-ui-design
description: Projetar e revisar interfaces visuais de sistemas, dashboards e aplicações com hierarquia, layout, tokens, componentes, densidade, estados e responsividade. Use para telas, dashboards, design systems, layouts, tabelas, formulários e navegação; combine com UX e acessibilidade quando houver fluxo ou interação.
---

# Design de interface

## Quando usar

- Acionar para definir ou revisar hierarquia, grid, shell, densidade, tokens,
  estados visuais, tabelas, formulários e navegação de uma interface.
- Acionar quando uma tela funciona, mas a composição dificulta escaneamento,
  comparação, priorização ou recuperação de erros.
- Não acionar para descobrir se o fluxo resolve a necessidade da pessoa; usar
  `$specsfy-specialist-ux-design` para pesquisa, jornada e teste de tarefa.
- Combinar com `$specsfy-specialist-react-ui-components` quando a implementação
  React puder partir de uma referência TSX copiável.

## Fluxo

1. Inspecionar produto, design system, tokens, componentes, breakpoints e
   screenshots atuais antes de propor uma linguagem nova.
2. Identificar pessoa, tarefa principal, frequência, dispositivo, densidade e
   custo do erro; ordenar conteúdo e ações por essa prioridade.
3. Inventariar dados, unidades, permissões e estados nominal, loading, empty,
   partial, error, offline e permission denied antes do layout.
4. Escolher shell, navegação e grid coerentes com a arquitetura da informação;
   usar a matriz em [references/standards.md](references/standards.md).
5. Definir hierarquia por agrupamento, contraste, escala e espaço e mapear cada
   decisão para tokens semânticos.
6. Implementar ou especificar componentes e casos extremos em todos os
   breakpoints sem criar variantes equivalentes às já existentes.
7. Validar conteúdo real, legibilidade, responsividade, acessibilidade e
   consistência com evidência visual e comportamental.

Quando a implementação usar React, carregar
`$specsfy-specialist-react-ui-components` depois de definir a composição para
escolher referências TSX sem transferir a decisão visual para o catálogo de
exemplos.

## Padrões

- Dashboard responde perguntas; não é coleção de cards decorativos.
- Colocar visão geral antes do detalhe e ação junto do objeto afetado.
- Usar tabela para comparação densa, lista para leitura e cards para entidades distintas.
- Preservar posição, filtros e contexto ao navegar entre lista e detalhe.
- Exibir unidade, período, origem, atualização e vazio nos dados.
- Manter ação destrutiva distinta, explicada e reversível quando possível.
- Definir tokens semânticos e uma escala limitada de spacing/tipografia.

## Antipadrões

- Distribuir métricas em cards idênticos sem pergunta, período ou comparação;
  a tela exibe números, mas não permite interpretar variação ou prioridade.
- Criar uma nova cor, spacing ou variante para cada tela; o design system perde
  vocabulário comum e torna mudanças globais imprevisíveis.
- Usar placeholder como label, ícone sem texto acessível ou cor como único
  estado; o significado desaparece conforme interação e acessibilidade.
- Esconder ações frequentes em menus para obter uma tela “limpa”; aumenta custo
  operacional e reduz descoberta sem diminuir complexidade real.

## Validação

- Comparar cenários nominal, loading, empty, partial, error, offline e
  permission denied na mesma composição.
- Exercitar conteúdo curto/longo, números extremos, tradução expandida e
  preferências de data, moeda e timezone.
- Verificar viewport mínimo suportado, zoom 200%, reflow, contraste, teclado,
  foco e reduced motion.
- Auditar tokens e componentes novos contra os já publicados e justificar
  qualquer duplicação.
- Revisão final conjunta com `$specsfy-specialist-react-ui-components` quando
  algum asset React tiver sido adaptado.
- Não declarar a interface consistente ou responsiva sem screenshots ou
  inspeção equivalente nos estados e viewports críticos.

## Skills relacionadas

- `$specsfy-specialist-nextjs` governa a fronteira server/client e o roteamento
  da interface; esta skill governa composição e estados visuais.
- `$specsfy-specialist-prototyping` testa alternativas de composição no menor
  nível de fidelidade necessário antes da implementação definitiva.
- `$specsfy-specialist-shadcn-ui` fornece primitives e variantes; esta skill
  decide hierarquia e coerência do sistema que os utiliza.
- `$specsfy-specialist-ux-design` governa pesquisa, jornada, arquitetura da
  informação e validação de tarefas.
- `$specsfy-specialist-react-ui-components` fornece exemplos TSX depois que a
  composição e a hierarquia estão definidas.
- `$specsfy-specialist-web-accessibility` conduz auditoria WCAG, teclado e
  tecnologia assistiva.
- `$specsfy-specialist-tailwind-css` traduz tokens e variantes para utilitários
  quando essa é a stack observada.

Leia [references/standards.md](references/standards.md) para matrizes de layout,
densidade, dados, tokens, estados e critérios de revisão visual.
