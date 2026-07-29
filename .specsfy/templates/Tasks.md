### 14. Tarefas

Formato:
`- [ ] TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Checklist obrigatório por tarefa, na ordem:

```markdown
  - [ ] **PREP**: Confirmar escopo, IDs, dependências e baseline.
  - [ ] **EXECUTE**: Produzir a entrega no caminho declarado.
  - [ ] **VERIFY**: Executar a verificação focal adequada.
  - [ ] **EVIDENCE**: Registrar comando, resultado e IDs nas seções 11–13.
  - [ ] **IMPROVE**: Registrar melhoria aplicada ou ausência justificada.
```

#### Fase 1 — RED TDD informado pelo BDD

- [ ] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Pest falhando em tests/Feature/RecursoTest.php — Refs: US-001, FR-001, NFR-001, AC-001 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [ ] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Pest falhando em tests/Feature/RecursoTest.php — Refs: US-001, FR-001, NFR-001, AC-002 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [ ] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Pest falhando em tests/Feature/RecursoTest.php — Refs: US-001, FR-001, NFR-001, AC-003 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [ ] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

#### Fase 2 — US-001 [título] (P1)

**Objetivo**: [valor entregue].
**Teste independente**: [comando e resultado].

- [ ] T004 [CODE] [US-001] Implementar comportamento em app/Services/RecursoService.php — Refs: US-001, FR-001, NFR-001, AC-001, AC-002, AC-003 — Depends: T001, T002, T003
  - [ ] **PREP**: Confirmar RED TDD e dependências.
  - [ ] **EXECUTE**: Implementar a menor mudança.
  - [ ] **VERIFY**: Executar testes focais e regressão.
  - [ ] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T004","refs":["US-001","FR-001","NFR-001","AC-001","AC-002","AC-003"],"files":["app/Services/RecursoService.php"],"commands":[{"run":"comando focal","exit":0}]} -->

O comentário é obrigatório para tarefa `[CODE]` concluída quando a spec declara
`Evidence Contract: 1`; ele permanece dentro da fonte única.

**Checkpoint**: [como demonstrar a história isoladamente].

#### Fase final — Qualidade

- [ ] T005 [TEST] Executar regressão e rastreabilidade em tests/Feature/RecursoTest.php — Refs: US-001, FR-001, NFR-001, AC-001, AC-002, AC-003 — Depends: T004
  - [ ] **PREP**: Identificar suites, checks e gates.
  - [ ] **EXECUTE**: Executar regressão e rastreabilidade.
  - [ ] **VERIFY**: Confirmar ausência de gaps.
  - [ ] **EVIDENCE**: Registrar contagens e comandos finais.
  - [ ] **IMPROVE**: Registrar retrospectiva do processo.

### 15. Ordem de execução

- Caminho crítico: T001/T002/T003 → T004 → T005.
- Tarefas paralelas: [IDs e motivo, ou “Nenhuma”.]
- Estratégia de MVP: [menor conjunto de histórias entregável].
