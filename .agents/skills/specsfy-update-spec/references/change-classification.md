# Classificar uma atualização de spec

Leia esta referência quando um pedido chegar depois de a spec já ter obtido
`Definition Gate: Passed`.

| Classe | Sinal observável | Ação | Retomada |
| --- | --- | --- | --- |
| Correção interna | não muda saída, contrato, dado, risco ou aceite | não editar a spec; registrar na evidência | `implement` |
| Esclarecimento editorial | mesma decisão e mesmos testes continuam suficientes | ajustar redação sem invalidar gates | origem |
| Mudança de comportamento | muda resultado, ator, escopo, AC, FR, NFR, dados, segurança ou interface | atualizar a spec e reabrir Ato I | `validate` |
| Mudança de plano | mantém o comportamento aprovado, mas muda solução, tarefa ou estratégia TDD | atualizar a spec e reabrir Ato II | `tasks` |
| Nova fatia | possui finalidade, atores ou entrega demonstrável independentes | não ampliar a spec atual; encaminhar a backlog ou nova spec | `backlog` ou `specify` |
| Decisão ausente | duas respostas plausíveis mudam comportamento, risco ou teste | perguntar uma decisão por vez | `backlog`, depois `update-spec` |

## Regras de decisão

- Classifique pelo efeito, não pelas palavras “pequeno”, “rápido” ou “só”.
- Trate remoção de comportamento aprovado como mudança de comportamento.
- Trate compatibilidade, privacidade, autorização e persistência como Ato I.
- Trate mudança de biblioteca sem efeito normativo como Ato II.
- Quando uma mudança tocar áreas de classes diferentes, use a reabertura mais
  anterior.
- Em dúvida entre esclarecimento editorial e comportamento, reabra o Ato I.
- Uma nova fatia exige intenção explícita antes de criar outra spec.
