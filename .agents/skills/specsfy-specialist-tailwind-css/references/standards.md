# Padrões e referências Tailwind CSS

## Camadas do sistema

| Camada | Papel | Exemplo |
| --- | --- | --- |
| Tokens | Valores e papéis compartilhados (cor, espaçamento, radius, tipografia) | `--color-surface`, escala de `spacing` |
| Primitivos | Layout, tipografia e comportamento básico reaproveitável | `flex`, `grid`, `text-sm`, `rounded-md` |
| Componentes | Composição semântica reconhecível no framework | `Card`, `Badge`, `Button` |
| Variantes | Estado e contexto declarados sobre um primitivo/componente | `hover:`, `data-[state=open]:`, `aria-selected:` |

Construa de cima para baixo ao consumir (componente antes de utilitário
solto) e de baixo para cima ao decidir extrair (utilitário repetido vira
componente só quando representa uma unidade semântica, não uma coincidência
visual).

## Configuração por geração

- Tailwind v3 e anteriores: tokens em `tailwind.config.js`
  (`theme.extend`), plugins registrados no config, diretivas `@tailwind
  base/components/utilities` no CSS de entrada.
- Tailwind v4: tokens declarados diretamente em CSS via `@theme`, uma única
  diretiva `@import "tailwindcss"`, detecção de conteúdo automática por
  padrão (menos necessidade de `content` explícito). Não misture sintaxe de
  configuração entre as duas gerações sem confirmar a versão instalada no
  lockfile.
- `compatibility`/guia de upgrade oficial lista as mudanças de default
  (cores, `ring`, `border`) entre versões majors — checar antes de migrar um
  projeto existente.

## Detecção de classes

- O scanner de conteúdo do Tailwind lê os arquivos-fonte como texto e
  procura por strings que pareçam classes; ele não executa JavaScript.
- Classes montadas por concatenação parcial (`` `bg-${color}-500` ``,
  `` `p-${size}` ``) nunca são detectadas — o texto `bg-${color}-500` não
  contém nenhuma classe completa. Use um mapa literal
  (`{ red: "bg-red-500", blue: "bg-blue-500" }`) para que cada string
  completa apareça no código-fonte.
- Classes vindas de uma biblioteca externa ou de HTML gerado fora dos
  arquivos escaneados (CMS, template remoto) precisam estar na configuração
  de `content`/`source` explicitamente, ou não entram no CSS final.

## Responsividade e container queries

- Mobile-first: a classe sem prefixo de breakpoint é a base; `sm:`, `md:`,
  `lg:`, `xl:`, `2xl:` sobrepõem a partir daquele breakpoint para cima.
- `@container` (com um ancestral marcado `@container` e utilitários
  `@sm:`/`@md:` no próprio Tailwind) resolve o caso em que o componente
  precisa responder ao tamanho do contêiner (uma sidebar, um painel
  redimensionável), não ao viewport da janela.
- Zoom e reflow são requisitos de acessibilidade tratados como
  responsividade: o layout não pode exigir scroll horizontal a 400% de zoom
  (equivalente a uma viewport de 320px CSS de largura) para conteúdo que
  normalmente rola só verticalmente.

## Variantes de estado e preferência

- Estado de interação: `hover:`, `focus:`, `focus-visible:` (preferir
  `focus-visible` a `focus` puro para não mostrar anel de foco em clique de
  mouse), `active:`, `disabled:`.
- Estado de dado/aria: `aria-selected:`, `aria-expanded:`,
  `data-[state=open]:` quando o componente expõe atributo de estado (comum
  em Radix/shadcn).
- Preferência do usuário: `dark:` (tema), `motion-reduce:`/`motion-safe:`
  (`prefers-reduced-motion`), `contrast-more:` (`prefers-contrast`),
  `forced-colors:` (Windows High Contrast Mode) — tratar como parte do
  design, não como polish opcional.

## `@apply` — quando é aceitável

- Aceitável para um punhado de utilitários realmente repetidos em um único
  seletor de baixo nível (ex.: um reset local, uma classe de terceiros que
  não pode receber classes Tailwind diretamente).
- Não aceitável como estratégia geral de componentização — nesse caso, um
  componente do framework (React/Vue/Astro) com as classes inline resolve
  melhor: mantém colocation, permite variantes por prop e não recria uma
  folha de estilo paralela.

## Comandos de verificação

- `npx tailwindcss -i ./src/input.css -o ./dist/output.css --minify` gera o
  CSS final fora de um framework com build step próprio; inspecionar o
  arquivo gerado para confirmar que nenhuma classe usada ficou ausente.
- Em projetos com framework (Next.js, Astro, Vite), o build do próprio
  framework (`next build`, `astro build`, `vite build`) já invoca o
  PostCSS/Tailwind configurado — rodar esse build é a validação real, não
  apenas o servidor de desenvolvimento.
- `npx tailwindcss --help`/documentação do CLI lista as flags de watch e
  minify; confirmar a versão com `npx tailwindcss --version` antes de aplicar
  sintaxe de uma geração diferente da instalada.

## Fontes oficiais

- Documentação: https://tailwindcss.com/docs
- Theme variables (v4): https://tailwindcss.com/docs/theme
- Responsive design: https://tailwindcss.com/docs/responsive-design
- Dark mode: https://tailwindcss.com/docs/dark-mode
- Hover/focus/other states: https://tailwindcss.com/docs/hover-focus-and-other-states
- Container queries: https://tailwindcss.com/docs/responsive-design#container-queries
- Detecting classes in source files: https://tailwindcss.com/docs/detecting-classes-in-source-files
- Adding custom styles (`@apply`): https://tailwindcss.com/docs/adding-custom-styles
- Compatibility / upgrade guide: https://tailwindcss.com/docs/compatibility
