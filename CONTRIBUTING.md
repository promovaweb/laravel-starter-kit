# Contribuindo com o Laravel Starter Kit

Este guia é para quem altera, revisa ou mantém o [Laravel Starter Kit](https://github.com/promovaweb/laravel-starter-kit). Para instalar e usar o template, leia o [README](README.md).

A base usa [Laravel](https://github.com/laravel/framework) 13, [Inertia](https://github.com/inertiajs/inertia) 3, [React](https://github.com/react/react) 19, TypeScript, [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) 4 e [Pest](https://github.com/pestphp/pest) 5. O projeto também instala as skills do [Specsfy](https://github.com/promovaweb/specsfy) para o fluxo de especificação e de implementação.

## Antes de começar

- Converse no [Discord](https://promovaweb.com/discord) antes de trabalhar em uma mudança grande. Isso evita esforço em uma direção que o projeto não vai seguir.
- Abra uma [issue](https://github.com/promovaweb/laravel-starter-kit/issues) para cada mudança. Descreva o comportamento atual, o esperado e o passo para reproduzir.
- Mudanças de dependência, de estrutura de pastas ou de fluxo de autenticação precisam de alinhamento antes do código.
- Um pull request por assunto.

## Ambiente

Requisitos:

- PHP 8.3 ou superior, com as extensões exigidas pelo Laravel.
- Composer 2.
- Node.js 22 ou superior.
- npm.

Clone o repositório e prepare o ambiente:

```bash
git clone https://github.com/promovaweb/laravel-starter-kit.git
cd laravel-starter-kit
composer setup
```

O `composer setup` instala as dependências PHP, copia o `.env.example` para `.env`, gera a chave, roda as migrations, instala as dependências do frontend e compila os assets.

Para desenvolver:

```bash
composer run dev
```

O comando sobe o servidor PHP, o worker de filas, os logs com Pail e o Vite. Para rodar os processos separados, use `php artisan serve`, `php artisan queue:listen`, `php artisan pail` e `npm run dev`.

O banco local é SQLite em `database/database.sqlite`. O arquivo é criado na primeira execução das migrations. Os e-mails vão para o log. Para outro banco ou outro serviço, ajuste o `.env` local, que não é versionado.

Se as páginas não refletirem uma alteração de frontend, rode `npm run build` ou mantenha `npm run dev` em execução.

## Organização do código

```text
app/
  Actions/           ações do Fortify e de criação de equipe
  Concerns/          traits de validação e de vínculo com equipes
  Data/              objetos de permissões e de equipe atual
  Enums/             papéis e permissões de equipe
  Http/              controllers, middleware, requests e respostas
  Models/            User, Team, Membership e TeamInvitation
  Notifications/     convites de equipe por e-mail
  Policies/          autorização de equipe
  Providers/         serviços da aplicação e do Fortify
  Rules/             validações de nome de equipe e de convite
resources/js/
  pages/             páginas Inertia de autenticação, configurações e equipes
  layouts/           layouts de aplicação, autenticação e configurações
  components/        componentes de interface, incluindo ui/
  hooks/             hooks de aparência, navegação, dois fatores e feedback
  types/             tipos compartilhados do frontend
  actions/           gerado pelo Wayfinder, não edite à mão
  routes/            gerado pelo Wayfinder, não edite à mão
  wayfinder/         tipos gerados pelo Wayfinder, não edite à mão
routes/              rotas web, de configurações e de console
database/            migrations, factories e seeders
tests/               testes Pest de Feature e Unit
.agents/skills/      skills instaladas para agentes
.specsfy/            contexto persistente e specs do Specsfy
brand/               identidade visual do starter kit
```

O backend concentra autenticação, autorização, persistência e fluxo de equipes. O frontend concentra páginas, formulários, navegação e feedback.

Os artefatos em `resources/js/actions`, `resources/js/routes` e `resources/js/wayfinder` são gerados pelo [Laravel Wayfinder](https://github.com/laravel/wayfinder) durante `npm run dev` e `npm run build`. Não edite esses arquivos. Importe as funções de `@/actions` e `@/routes`.

O contexto técnico está em [PROJECT.md](PROJECT.md) e em `.specsfy/STACK.md`. O mapa de dados está em `.specsfy/DATABASE.md`.

## Fluxo de trabalho

O projeto usa o [Specsfy](https://github.com/promovaweb/specsfy) para mudanças que precisam de especificação:

1. Capture a ideia em `specs/inbox/`.
2. Refine o item em `specs/backlog/`.
3. Promova a spec para `specs/specs/<NNNN>-<slug>/spec.md`.
4. Planeje as tarefas na própria spec.
5. Implemente e valide.

Mudanças pequenas, como correção de texto, ajuste de estilo ou correção de bug com teste, podem ir direto para uma branch e um pull request com issue.

Para uma mudança comum de domínio:

1. Crie a branch a partir da `main`.
2. Crie a migration e o model com `php artisan make:migration` e `php artisan make:model`.
3. Atualize as factories e os seeders.
4. Crie o controller, o request e a policy quando houver autorização.
5. Registre a rota em `routes/web.php` ou `routes/settings.php`.
6. Crie ou ajuste a página em `resources/js/pages`.
7. Escreva o teste em `tests/Feature`.
8. Rode as validações e abra o pull request.

Para uma mudança de interface, use os componentes de `resources/js/components/ui` antes de criar um componente novo. Preserve os tokens e os temas definidos em `resources/css/app.css` e em `brand/`.

## Regras do código

- Escreva código, comentários e textos de interface em português do Brasil. Preserve termos técnicos em inglês quando forem o nome usado pelo ecossistema.
- Siga o estilo do arquivo ao redor. Use nomes descritivos para variáveis e métodos.
- Em PHP, use tipos de retorno e tipos nos parâmetros. Prefira promoção de construtor e blocos PHPDoc a comentários soltos.
- Em TypeScript, preserve os tipos e evite `any` sem justificativa.
- Use as páginas em `resources/js/pages` e o `Inertia::render()` para as respostas. Não crie views Blade para telas da aplicação.
- Use as funções do Wayfinder em vez de montar URLs à mão no frontend.
- Não adicione dependência sem alinhamento com a mantenedora.
- Não versione `.env`, chaves, banco local nem artefatos de build.
- Segredos ficam no `.env` e nas configurações do ambiente. Nunca no código, nos testes ou nos exemplos.
- Não altere à mão os arquivos gerados pelo Wayfinder, pelo Boost ou pelas skills do Specsfy.
- Toda mudança precisa de teste. Corrija o teste existente ou escreva um novo em `tests/`.

## Validar

O comando completo, igual ao do CI:

```bash
composer ci:check
```

Ele roda ESLint, Prettier, TypeScript, Pint, PHPStan e Pest. O workflow `.github/workflows/tests.yml` executa `composer setup` e depois `composer ci:check` em PHP 8.4 e Node 22.

Comandos por área:

| Comando | O que cobre |
| --- | --- |
| `composer test` | Pint, PHPStan e Pest |
| `composer lint` | corrige o estilo PHP com Pint |
| `composer lint:check` | confere o estilo PHP sem alterar |
| `composer types:check` | análise estática com PHPStan nível 7 |
| `php artisan test --compact` | testes Pest |
| `php artisan test --compact --filter=NomeDoTeste` | um teste específico |
| `npm run lint` | corrige o frontend com ESLint |
| `npm run lint:check` | confere o frontend sem alterar |
| `npm run format` | formata `resources/` com Prettier |
| `npm run format:check` | confere a formatação sem alterar |
| `npm run types:check` | checagem de tipos com `tsc` |
| `npm run build` | build de produção com Vite |
| `npm run build:ssr` | build do cliente e do SSR |

Rode o mínimo que cobre a mudança durante o trabalho. Antes do pull request, rode `composer ci:check`.

## Documentação

- `README.md`: instalação e uso do template.
- `CONTRIBUTING.md`: este guia.
- `PROJECT.md`: história, finalidade, capacidades e limites do projeto.
- `.specsfy/`: stack, regras, banco e specs.
- `CHANGELOG.md`: histórico de versões.
- <https://promovaweb.com/docs/>: documentação publicada no site.

Depois de uma implementação conduzida pelo Specsfy, reconstrua a documentação técnica em `docs/` com a skill `specsfy-documentator`. A pasta `docs/` ainda não existe no repositório. Quando ela for criada, mantenha o conteúdo alinhado ao código.

Mudanças de comando, configuração ou fluxo também pedem atualização do `README.md` ou deste guia.

## Commits e pull requests

Use mensagens no formato `tipo(escopo): descrição`, no imperativo e em português. Exemplos de tipo: `feat`, `fix`, `docs`, `test`, `refactor` e `chore`.

```text
feat(teams): permite cancelar convite pendente
fix(auth): corrige redirecionamento após o login
docs: atualiza o guia de contribuição
```

O pull request deve trazer:

- a descrição do problema e da solução;
- a issue relacionada;
- os comandos de validação executados;
- capturas de tela quando a mudança for visual;
- a indicação de migration ou de mudança de configuração.

Não inclua trailer de coautoria de IA nos commits. Não faça merge sem o CI verde.

## Releases

A versão vive na tag Git e no `CHANGELOG.md`. O workflow `.github/workflows/release.yml` valida o changelog e publica a GitHub Release a partir da seção da versão.

O `CHANGELOG.md` precisa manter a seção `## [Não lançado]` no topo. Para publicar:

1. Logo abaixo de `## [Não lançado]`, crie a seção `## [x.y.z] - AAAA-MM-DD` com as mudanças da versão. Mantenha o título `## [Não lançado]`, porque o workflow falha sem ele.
2. Faça commit e push na `main`.
3. Crie e envie a tag anotada:

   ```bash
   git tag -a vx.y.z -m "Release vx.y.z"
   git push origin vx.y.z
   ```

4. Confira a release publicada:

   ```bash
   gh release view vx.y.z
   ```

Não crie a GitHub Release à mão. O workflow para com erro quando a release da tag já existe.

Também é possível disparar o workflow `Release` pela interface do GitHub, com a opção `publicar` marcada e a versão informada. O workflow cria a tag e a release nesse caso.

O projeto usa versionamento semântico. Mudanças incompatíveis pedem versão maior.

## Licença

O campo `license` do `composer.json` declara a licença MIT. Ao enviar uma contribuição, você concorda que ela segue essa licença.
