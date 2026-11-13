<p align="center">
  <a href="https://github.com/promovaweb/laravel-starter-kit">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/promovaweb/laravel-starter-kit/main/brand/logo/logo-dark.png">
      <img alt="Laravel Starter Kit" src="https://raw.githubusercontent.com/promovaweb/laravel-starter-kit/main/brand/logo/logo-light.png" width="420">
    </picture>
  </a>
</p>

<h1 align="center">Laravel Starter Kit</h1>

<p align="center">
  Um ponto de partida Laravel com Inertia, React, autenticação, passkeys e equipes para iniciar aplicações web sem refazer o básico.
</p>

<p align="center">Um projeto da <a href="https://promovaweb.com">Promovaweb</a></p>

<p align="center">
  <a href="https://github.com/promovaweb/laravel-starter-kit/releases/latest"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/promovaweb/laravel-starter-kit"></a>
  <a href="https://github.com/promovaweb/laravel-starter-kit/actions/workflows/tests.yml"><img alt="Testes" src="https://github.com/promovaweb/laravel-starter-kit/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="Licença" src="https://img.shields.io/github/license/promovaweb/laravel-starter-kit"></a>
</p>

<p align="center">
  <a href="https://promovaweb.com/discord"><img alt="Discord: obter ajuda e conversar com a Comunidade" src="https://img.shields.io/badge/Discord-Obter%20ajuda%20e%20conversar%20com%20a%20Comunidade-5865F2?style=for-the-badge&logo=discord&logoColor=white"></a>
</p>

<p align="center">
  <a href="https://promovaweb.com/docs/">Documentação</a> ·
  <a href="https://promovaweb.com/discord">Discord</a> ·
  <a href="https://promovaweb.com/planos?utm_source=github&utm_medium=readme&utm_campaign=laravel-starter-kit">Planos da Promovaweb</a> ·
  <a href="CHANGELOG.md">Changelog</a>
</p>

## O que é

O Laravel Starter Kit é o template da Promovaweb para começar aplicações Laravel com o trabalho transversal pronto. Ele reúne autenticação com [Laravel Fortify](https://github.com/laravel/fortify), passkeys, autenticação de dois fatores, verificação de e-mail, perfil, aparência, equipes com papéis, convites e dashboard.

O backend usa [Laravel](https://github.com/laravel/framework) 13. O frontend usa [React](https://github.com/react/react) 19 com [Inertia](https://github.com/inertiajs/inertia) 3, TypeScript e [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) 4. A base é pequena, coberta por testes e pronta para receber as regras do seu produto.

| Área | O que já vem |
| --- | --- |
| Conta | registro, login, recuperação de senha, verificação de e-mail e confirmação de senha |
| Segurança | autenticação de dois fatores, passkeys, troca de senha e exclusão da conta |
| Equipes | equipe pessoal, equipes adicionais, convites por e-mail e papéis owner, admin e member |
| Perfil | nome, e-mail e preferências de aparência |
| Interface | layouts de aplicação e de autenticação, componentes e temas claro, escuro e sistema |
| Qualidade | Pest, PHPStan, Pint, ESLint, Prettier e TypeScript |

## Requisitos

- PHP 8.3 ou superior.
- Composer 2.
- Node.js 22 ou superior.
- npm.

O projeto usa SQLite por padrão. Para outro banco, ajuste `DB_CONNECTION` e as demais variáveis no `.env`.

## Instalação

O repositório é um template do GitHub. Crie sua aplicação de uma destas formas.

Use o botão **Use this template** em [promovaweb/laravel-starter-kit](https://github.com/promovaweb/laravel-starter-kit/generate), crie o seu repositório e clone o repositório criado. Para começar direto do repositório original:

```bash
git clone https://github.com/promovaweb/laravel-starter-kit minha-app
cd minha-app
```

Com o [Laravel Installer](https://github.com/laravel/installer) 5.18 ou superior, a opção `--using` também aceita a URL do repositório. O instalador baixa o template com `npx tiged`, sem o histórico Git. Em seguida, roda o `composer install`. Como o download usa o `npx`, esse caminho também exige o Node.js:

```bash
laravel new minha-app --using=https://github.com/promovaweb/laravel-starter-kit
cd minha-app
```

Em qualquer um dos caminhos, prepare o ambiente:

```bash
composer setup
```

O `composer setup` instala as dependências PHP, copia o `.env.example` para `.env`, gera a chave da aplicação, roda as migrations, instala as dependências do frontend e compila os assets.

### Atualizar

O projeto é um ponto de partida, não uma dependência. Não existe comando de atualização. Leia o [CHANGELOG](CHANGELOG.md) e traga para a sua aplicação as mudanças que interessam.

## Primeiros passos

Inicie o ambiente de desenvolvimento:

```bash
composer run dev
```

O comando sobe o servidor PHP, o worker de filas, os logs com Pail e o Vite. Abra <http://localhost:8000> e crie uma conta em `/register`. Ao criar a conta, você recebe uma equipe pessoal e entra no dashboard dessa equipe.

Para rodar cada processo em um terminal separado, use `php artisan serve`, `npm run dev`, `php artisan queue:listen` e `php artisan pail`.

## Uso

### Rotas principais

| Rota | Página |
| --- | --- |
| `/` | página inicial pública |
| `/register` e `/login` | cadastro e entrada |
| `/{current_team}/dashboard` | dashboard da equipe atual |
| `/settings/profile` | nome, e-mail e exclusão da conta |
| `/settings/security` | senha, autenticação de dois fatores e passkeys |
| `/settings/appearance` | tema claro, escuro ou sistema |
| `/settings/teams` | equipes, membros, convites e troca de equipe |

O segmento `{current_team}` é o slug da equipe atual. O middleware `SetTeamUrlDefaults` preenche esse valor nas rotas geradas pelo Laravel.

### Equipes e papéis

Cada conta recebe uma equipe pessoal no cadastro. A partir de `/settings/teams`, você cria outras equipes, convida pessoas por e-mail e alterna a equipe atual.

| Papel | Permissões |
| --- | --- |
| `owner` | todas as permissões, incluindo excluir a equipe e gerenciar membros |
| `admin` | atualizar a equipe, criar convites e cancelar convites |
| `member` | participa da equipe sem permissões administrativas |

Os convites valem por três dias. Uma tarefa agendada diária remove os convites expirados.

### Aparência

A tela `/settings/appearance` alterna entre claro, escuro e sistema. A escolha fica em um cookie e é aplicada antes da primeira pintura da página.

### Banco de dados

Depois de criar uma migration, rode:

```bash
php artisan migrate
```

Para recriar o banco local do zero, com os seeders:

```bash
php artisan migrate:fresh --seed
```

O comando apaga os dados do banco configurado no `.env`. Use apenas no ambiente local.

## Uso com agentes

O repositório já traz o servidor MCP do [Laravel Boost](https://github.com/laravel/boost) em `.mcp.json`:

```json
{
  "mcpServers": {
    "laravel-boost": {
      "command": "php",
      "args": ["artisan", "boost:mcp"]
    }
  }
}
```

Clientes que leem `.mcp.json` encontram o servidor sem configuração extra. O Boost expõe ferramentas de documentação, schema e consulta ao banco para o agente.

As skills do projeto ficam em `.agents/skills` e são controladas pelo `skills-lock.json`. Os comandos usam o [Skills CLI](https://github.com/vercel-labs/skills):

```bash
npm run skills:list      # lista as skills instaladas
npm run skills:restore   # reinstala as skills do lock
npm run skills:update    # atualiza as skills do projeto
```

As skills são versionadas no próprio repositório e vêm do [Specsfy](https://github.com/promovaweb/specsfy), o framework de especificação da Promovaweb.

## Documentação

- Guias e referência: <https://promovaweb.com/docs/>.
- Contexto do projeto: [PROJECT.md](PROJECT.md).
- Histórico de versões: [CHANGELOG.md](CHANGELOG.md) e [releases](https://github.com/promovaweb/laravel-starter-kit/releases).

## Feito com

| Projeto | Para quê |
| --- | --- |
| [Laravel](https://github.com/laravel/framework) | framework e regras de backend |
| [Inertia](https://github.com/inertiajs/inertia) | ligação entre as rotas Laravel e as páginas React |
| [React](https://github.com/react/react) | interface |
| [TypeScript](https://github.com/microsoft/TypeScript) | tipagem do frontend |
| [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) | estilos |
| [Vite](https://github.com/vitejs/vite) | build e servidor de desenvolvimento |
| [Laravel Fortify](https://github.com/laravel/fortify) | autenticação e dois fatores |
| [Laravel Passkeys](https://github.com/laravel/passkeys) | entrada com passkeys |
| [Laravel Wayfinder](https://github.com/laravel/wayfinder) | funções TypeScript para as rotas |
| [Radix UI](https://github.com/radix-ui/primitives) | componentes acessíveis |
| [Laravel Boost](https://github.com/laravel/boost) | MCP e skills para agentes |
| [Specsfy](https://github.com/promovaweb/specsfy) | skills de especificação e implementação |

## Comunidade e suporte

- **Discord:** [obter ajuda e conversar com a Comunidade](https://promovaweb.com/discord).
- **Bugs e pedidos:** abra uma [issue](https://github.com/promovaweb/laravel-starter-kit/issues) com a versão, o sistema operacional e o passo a passo para reproduzir.
- **Novidades:** acompanhe o [CHANGELOG](CHANGELOG.md) e as [releases](https://github.com/promovaweb/laravel-starter-kit/releases).

## Contribuir

Leia o [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir um pull request. Ele traz o ambiente, a organização do código, as regras e os comandos de validação.

## Promovaweb

O Laravel Starter Kit é mantido pela [Promovaweb](https://promovaweb.com), comunidade de co-working digital onde profissionais aprendem a construir, automatizar e gerir negócios de tecnologia e IA com aulas ao vivo, Co-works e revisão de projetos reais.

Quer usar o Laravel Starter Kit em projetos de verdade, com acompanhamento? Conheça os [planos da Promovaweb](https://promovaweb.com/planos?utm_source=github&utm_medium=readme&utm_campaign=laravel-starter-kit).

## Licença

Distribuído sob a [licença MIT](LICENSE), a mesma do starter oficial do
Laravel de que o projeto deriva. A licença não concede o uso do nome e do
logo do Laravel Starter Kit nem da marca Promovaweb.
