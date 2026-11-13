# Changelog

Todas as mudanças relevantes do Laravel Starter Kit são registradas neste
arquivo. O projeto usa versionamento semântico e publica GitHub Releases a
partir das entradas versionadas abaixo.

## [Não lançado]

## [0.2.0] - 2026-11-13

### Adicionado

- Adiciona o arquivo `LICENSE` com a licença MIT, a mesma do starter oficial
  do Laravel de que o projeto deriva, e declara o campo `license` no
  `package.json`.

### Documentação

- Inclui o badge de licença no `README.md` e explica a licença nas seções
  Licença do `README.md` e do `CONTRIBUTING.md`.

## [0.1.2] - 2026-11-13

### Documentação

- Cria o `README.md` para quem usa o template, com o cabeçalho da
  Promovaweb, o Discord, a documentação, os planos e os repositórios usados.
- Cria o `CONTRIBUTING.md` para quem contribui, com o ambiente, as regras do
  código, os comandos de validação e o fluxo de release.
- Adiciona o `.markdownlint.json` com os elementos HTML do cabeçalho.
- Restaura a seção `## [Não lançado]` exigida pelo workflow `Release`.

## [0.1.1] - 2026-08-21

### Adicionado

- Publica o sistema de identidade visual e as referências de marca do starter
  kit.


## [0.1.0] - 2026-07-29

### Funcionalidades

- Publica o template Laravel 13 com Inertia 3, React 19, autenticação,
  passkeys e equipes.
- Gerencia as skills do projeto por meio do `skills-lock.json` e dos comandos
  `skills:list`, `skills:restore` e `skills:update`.
- Instala o framework e as skills do Specsfy pelo repositório público da
  Promovaweb.

### Operação

- Valida o changelog em cada atualização da `main`.
- Publica tags e GitHub Releases por tag semântica ou execução manual do
  workflow `Release`.
