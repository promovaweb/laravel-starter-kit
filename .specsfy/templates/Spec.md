# Especificação integrada: {{SPEC_NAME}}

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | {{SPEC_ID}} |
| Slug | {{SPEC_NUMBER}}-{{SPEC_SLUG}} |
| Status | Draft |
| Definition Gate | Pending |
| Plan Gate | Pending |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Atualizada em | {{CURRENT_DATE}} |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

[Dor observável e contexto.]

#### Resultado desejado

[Mudança percebida pelo usuário ou negócio.]

#### Métricas de sucesso

- [Métrica mensurável com alvo.]

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: [pergunta investigada] → [conclusão e impacto].
- Para claim material, use: `**R-001** [critical] claim — Verdict: verified|refuted|unverifiable — Confidence: high|medium|low — Evidence: research/caminho#locator — Budget: usado/limite`. IDs são únicos, `usado ≤ limite` e a âncora deve existir.

#### Fontes e contexto consultados

- [Código, documento, stakeholder ou “Nenhuma fonte externa”.]

#### Documentação consultada

- [Título/serviço, versão/data, URL ou caminho local, tópicos relevantes.]

#### Artefatos de pesquisa armazenados

- `specs/specs/{{SPEC_NUMBER}}-{{SPEC_SLUG}}/research/[fonte]/`: [origem, versão/data, licença quando aplicável e propósito], ou “Nenhum artefato externo”.
- Toda fonte externa efetivamente consultada deve ter uma evidência local em `research/`; registre aqui o caminho e mantenha conclusões normativas no `spec.md`.

#### Dúvidas respondidas

- **Q**: [pergunta material] → **A**: [resposta incorporada].

#### Dúvidas abertas

- [Pergunta bloqueante ou “Nenhuma”.]

### 3. Escopo e atores

#### Incluído

- [Capacidade incluída.]

#### Fora de escopo

- [Limite explícito.]

#### Atores

- **[Ator]**: [objetivo, permissões ou responsabilidade].

### 4. Princípios e restrições do projeto

- **PR-001**: [regra de governança, qualidade ou arquitetura].

### 5. Histórias de usuário

#### US-001 — [título] (P1)

Como [ator], quero [capacidade], para [valor].

**Por que P1**: [valor e urgência].
**Teste independente**: [como demonstrar valor isoladamente].
**Requisitos**: FR-001

### 6. Cenários BDD de aceite

#### AC-001 — [comportamento]

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-001
Feature: [capacidade observável]

  Scenario: [caminho feliz aceito]
    Given [estado inicial]
    When [ação]
    Then [resultado observável]
```

#### AC-002 — [regra ou variação crítica]

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-002
Feature: [capacidade observável]

  Scenario: [regra ou variação crítica]
    Given [contexto alternativo]
    When [ação]
    Then [regra observável]
```

#### AC-003 — [falha ou limite material]

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-003
Feature: [capacidade observável]

  Scenario: [falha ou limite material]
    Given [condição de falha ou limite]
    When [ação]
    Then [tratamento observável]
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve [comportamento verificável].

#### Não funcionais

- **NFR-001**: [atributo mensurável]. **Verificação**: [teste, inspeção ou medição].

#### Erros e casos-limite

- [Condição] → [comportamento observável].

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- [Stack, arquitetura e convenções encontradas no repositório.]

#### Arquitetura e módulos

- [Componentes, responsabilidades, persistência e pontos de extensão.]

#### Migrations

- [Mudança de schema, ordem, rollback e compatibilidade ou “Não aplicável”.]

#### Models

- [Model, responsabilidade, invariantes e arquivo.]

#### Controllers e casos de uso

- [Controller/handler/use case, entrada, saída, autorização e arquivo.]

#### Views e experiência

- [Tela/componente, estados loading/empty/error/success, acessibilidade e arquivo.]

#### Queries e repositórios

- [Query/repository, filtros, paginação, índices, consistência e arquivo.]

#### Jobs e processamento assíncrono

- [Job/event consumer, retry, idempotência e dead-letter ou “Não aplicável”.]

#### Estrutura de arquivos

```text
specs/specs/{{SPEC_NUMBER}}-{{SPEC_SLUG}}/
  spec.md
  research/
src/
tests/
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| [Entidade] | [chave] | [campos, validações] | [cardinalidade] |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| [Entidade] | [estado] | [evento] | [estado] | [regra] |

#### Migração e retenção

- [Estratégia ou “Não aplicável”.]

### 10. Interfaces e contratos

#### APIs expostas

- [Método/rota ou evento, autenticação, request, response, erros e versionamento.]

#### APIs externas utilizadas

- [Serviço, operação, versão, autenticação, timeout, retry e fallback ou “Nenhuma”.]

#### Documentação das APIs consultadas

- [Título, versão/data, URL ou caminho local e decisões extraídas.]

#### Eventos e outros contratos

- [Schema, produtor, consumidor, compatibilidade ou “Não aplicável”.]

### 11. Estratégia TDD

- **Unidade**: [regras e componentes].
- **Integração/contrato**: [fronteiras].
- **BDD/aceite**: [Gherkin de referência que orienta o entendimento e o desenho dos testes TDD].
- **Runner TDD**: [PHP = Pest; Node = decisão confirmada com o usuário e
  materializada em `test:tdd`; outra stack = runner existente ou decisão explícita].
- **E2E**: [jornadas essenciais ou “Não aplicável”.]
- **Verificação manual**: [somente o inevitável, com motivo].

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, NFR-001, AC-001 | [AC-001 na seção 6] | [caso 1 em tests/Feature/RecursoTest.php com marcador próprio `SPECSFY:`] | Pending | Pending | Pending |
| US-001, FR-001, NFR-001, AC-002 | [AC-002 na seção 6] | [caso 2 em tests/Feature/RecursoTest.php com marcador próprio `SPECSFY:`] | Pending | Pending | Pending |
| US-001, FR-001, NFR-001, AC-003 | [AC-003 na seção 6] | [caso 3 em tests/Feature/RecursoTest.php com marcador próprio `SPECSFY:`] | Pending | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | [tests/arquivo] | Pending |
| FR-001 | AC-002 | [nível] | [tests/arquivo] | Pending |
| FR-001 | AC-003 | [nível] | [tests/arquivo] | Pending |
| NFR-001 | AC-001 | [nível] | [comando] | Pending |
| NFR-001 | AC-002 | [nível] | [comando] | Pending |
| NFR-001 | AC-003 | [nível] | [comando] | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Pending
- **Comando**: `python3 .agents/skills/specsfy-04-validate/scripts/validate_spec.py specs/specs/{{SPEC_NUMBER}}-{{SPEC_SLUG}}/spec.md`
- **Achados**: [Pending.]
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `python3 .agents/skills/specsfy-05-tasks/scripts/validate_tasks.py specs/specs/{{SPEC_NUMBER}}-{{SPEC_SLUG}}/spec.md`
- **Achados**: [Pending.]

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `python3 .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.py specs/specs/{{SPEC_NUMBER}}-{{SPEC_SLUG}}/spec.md .`
- **Achados**: [Pending.]

### 14. Tarefas

Formato:
`- [ ] TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Cada tarefa possui exatamente este checklist, atualizado durante a execução:

```markdown
  - [ ] **PREP**: Confirmar escopo, IDs, dependências e baseline.
  - [ ] **EXECUTE**: Produzir a entrega no caminho declarado.
  - [ ] **VERIFY**: Executar a verificação focal adequada.
  - [ ] **EVIDENCE**: Registrar comando, resultado e IDs nas seções 11–13.
  - [ ] **IMPROVE**: Registrar melhoria aplicada ou ausência justificada.
```

#### Fase 1 — RED TDD informado pelo BDD

- [ ] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Pest falhando em tests/Feature/RecursoTest.php — Refs: US-001, FR-001, NFR-001, AC-001 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [ ] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [ ] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Pest falhando em tests/Feature/RecursoTest.php — Refs: US-001, FR-001, NFR-001, AC-002 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [ ] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [ ] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Pest falhando em tests/Feature/RecursoTest.php — Refs: US-001, FR-001, NFR-001, AC-003 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [ ] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

#### Fase 2 — US-001 [título] (P1)

**Objetivo**: [valor entregue].
**Teste independente**: [comando e resultado].

- [ ] T004 [CODE] [US-001] Implementar comportamento em app/Services/RecursoService.php — Refs: US-001, FR-001, NFR-001, AC-001, AC-002, AC-003 — Depends: T001, T002, T003
  - [ ] **PREP**: Confirmar RED TDD e dependências.
  - [ ] **EXECUTE**: Implementar a menor mudança.
  - [ ] **VERIFY**: Executar testes focais e regressão.
  - [ ] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T004","refs":["US-001","FR-001","NFR-001","AC-001","AC-002","AC-003"],"files":["app/Services/RecursoService.php"],"commands":[{"run":"comando focal","exit":0}]} -->

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

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- [Dependência ou “Nenhuma”.]

#### Riscos

- [Risco] → [mitigação].

#### Suposições

- [Default assumido.]

### 17. Decisões

- **DEC-001**: [decisão] — [razão, alternativas e trade-off].

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
