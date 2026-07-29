# Diretrizes publicáveis do framework

- Fonte canônica: `skills/AGENTS.md` do monorepo `promovaweb/specsfy`, bloco
  `specsfy:framework`.
- Observado em: 2026-07-27.
- Adaptação: nenhuma; o conteúdo delimitado abaixo deve permanecer idêntico à
  fonte.

<!-- specsfy:framework:start -->
## Framework Specsfy

Leia e siga integralmente `{{SPECSFY_SPEC_PATH}}` antes de trabalhar com
backlogs, refinamentos do backlog, especificações, tarefas, testes ou implementação. Esse
arquivo contém o fluxo, os caminhos canônicos e os gates do framework.

- Preserve as instruções próprias deste projeto.
- Leia `PROJECT.md`, `.specsfy/STACK.md`, `.specsfy/RULES.md` e
  `.specsfy/DATABASE.md` como contexto persistente antes de planejar mudanças.
- Execute `$specsfy-setup` quando algum desses arquivos estiver ausente.
- Execute o monitor de contexto no início, após cada tarefa e antes de concluir
  a entrega; resolva todo resultado `PENDING`.
- Use as skills `specsfy-aux-*` para manter stack, regras e banco sem apagar
  conteúdo humano.
- Execute `$specsfy-documentator` depois de cada implementação para reconstruir
  a documentação técnica completa em `docs/`.
- Use `specs/inbox/` para capturas imediatas ainda não refinadas.
- Use `specs/backlog/` para itens refináveis ainda não promovidos.
- Use `specs/specs/<NNNN>-<slug>/spec.md` como fonte normativa de cada fatia.
- Não crie `plan.md`, `tasks.md`, `research.md` ou outra fonte normativa
  paralela.
<!-- specsfy:framework:end -->
