# Qualidade e refinamento do backlog

Leia esta referência ao organizar, refinar, priorizar ou avaliar a prontidão de
um item. O backlog conecta necessidades de negócio ao trabalho verificável de
produto, desenvolvimento e testes. Ele não é uma lista solta de telas ou
funcionalidades e não substitui a `spec.md`.

## Hierarquia e tipos

Use a hierarquia somente até o nível que ajuda a navegação:

```text
Produto
└── Épico
    └── Funcionalidade
        ├── História ou requisito
        ├── Regra
        ├── Item técnico
        └── Melhoria
```

- **Épico** representa um objetivo amplo e agrupador.
- **Funcionalidade** delimita uma capacidade do produto.
- **História ou requisito** descreve uma entrega menor e verificável.
- **Regra** explicita uma restrição transversal ou de negócio.
- **Técnico** viabiliza qualidade, operação ou entregas dependentes.
- **Melhoria** incrementa uma capacidade existente.

Não force todos os níveis quando a relação ainda for desconhecida. Registre `A
esclarecer` e preserve a ideia.

Uma visão resumida pode combinar ordem, prioridade e tipo:

| Ordem | Prioridade | Tipo | Item | Objetivo |
| --- | --- | --- | --- | --- |
| 1 | Alta | Épico | Gestão de usuários | Administrar acesso |
| 2 | Alta | História | Realizar login | Acessar áreas privadas |
| 3 | Alta | Regra | Controlar permissões | Restringir operações |
| 4 | Média | Técnico | Processar notificações em fila | Evitar requisições lentas |
| 5 | Baixa | Melhoria | Preferências de notificação | Escolher canais |

## Anatomia adaptativa

Um item pode conter:

- título claro;
- contexto do problema;
- objetivo ou história do usuário;
- comportamento esperado;
- regras de negócio;
- critérios de aceitação;
- segurança, privacidade, desempenho, volume, auditoria e observabilidade;
- dependências;
- situações de erro e exceções;
- dentro e fora de escopo;
- tipo e prioridade.

A profundidade acompanha risco e complexidade. Capture primeiro; refine quando
a decisão for necessária. Não invente um campo para produzir aparência de
completude.

### Captura mínima

Antes de persistir um item, confirme somente:

- problema percebido;
- pessoa afetada ou beneficiada;
- resultado ou valor esperado;
- contexto suficiente para distinguir a ideia.

Reaproveite tudo o que já estiver claro no pedido. Se faltar algo ou houver
mais de uma interpretação material, pergunte uma lacuna por vez e reavalie
depois da resposta. Não persista placeholders nesses quatro campos e não
invente respostas. Hierarquia, prioridade, regras detalhadas, aceite e solução
técnica não pertencem a esse mínimo.

### Duplicatas e referências

Pesquise termos do pedido em backlogs, specs e documentação do projeto antes de
criar um item. Compare problema, pessoa, resultado e contexto para separar
possível duplicata de mera semelhança lexical. Specs e documentação podem
fornecer vocabulário, decisões vigentes e limites; não substituem a intenção
declarada pelo usuário.

Confirme se uma possível duplicata deve receber atualização ou se a nova ideia
possui uma diferença real. Registre caminhos e relações úteis em `Referências
relacionadas`; não funda, mova ou apague itens sem confirmação.

## Padrões de análise

### Autenticação

Considere estado da conta, comparação de identidade, proteção de credenciais,
limite de tentativas, sessão, desativação, mensagens seguras e autorização.
“Criar login” ou “criar tela” não descreve esse comportamento.

### Notificações

Defina propriedade, contagem, momento de leitura, ação individual e em lote,
histórico e isolamento entre usuários. Transforme “zerar ao ler” em um evento
objetivo: abrir menu, abrir item ou marcar tudo.

### Permissões

Quando operação, perfil, organização e alvo se combinarem, use uma matriz.
Autorize no servidor, impeça autoelevação, proteja invariantes como o último
administrador e registre mudanças sensíveis em auditoria.

| Operação | Admin | Manager | Member |
| --- | --- | --- | --- |
| Listar usuários | Sim | Mesma organização | Não |
| Editar member | Sim | Mesma organização | Não |
| Editar admin | Sim | Não | Não |
| Elevar o próprio perfil | Não | Não | Não |

### Pagamentos e integrações

Descreva fluxo principal, estados e transições, idempotência, autenticação de
callbacks, retries, falhas externas, vínculo com entidades internas e proteção
de credenciais e dados sensíveis.

Exemplo de fluxo: receber valor → solicitar cobrança → vinculá-la ao cliente →
apresentar PIX → confirmar por webhook autenticado → atualizar o estado uma
única vez. Modele ao menos pendente, paga, expirada, cancelada e falhou, sem
permitir que uma cobrança paga volte a pendente.

### Exportações e processamento pesado

Considere filtros, autorização por campo, fuso horário, limite para execução
síncrona, processamento em segundo plano, expiração, notificação e exposição de
dados sensíveis.

## Funcional e não funcional

Requisito funcional descreve o que acontece: autenticar, cobrar, notificar,
exportar ou cancelar. Requisito não funcional define uma condição mensurável de
qualidade e operação: latência, volume, isolamento, criptografia, auditoria,
retenção ou recuperação após falha.

Substitua adjetivos vagos por condições verificáveis. Exemplo: “responder em
até dois segundos para consultas de até 50 mil registros no ambiente de
produção definido pelo projeto”.

## Critérios de aceitação

Escreva condições observáveis, sem prescrever a implementação:

```gherkin
Scenario: Login de uma conta ativa
  Given uma conta ativa com credenciais válidas
  When a pessoa informa e-mail e senha corretos
  Then o acesso é autorizado conforme seu perfil

Scenario: Repetição de um webhook de pagamento
  Given uma cobrança já confirmada como paga
  When o mesmo evento autenticado é recebido novamente
  Then nenhum pagamento adicional é registrado
```

Na captura inicial, cenários podem permanecer ausentes. Para um item refinado,
use-os quando forem a forma mais clara de tornar sucesso, falha ou limite
verificável.

## Priorização

Ordene os itens considerando:

1. valor para usuário ou negócio;
2. risco de segurança, privacidade ou operação;
3. dependências e quantidade de entregas desbloqueadas;
4. urgência;
5. esforço;
6. incerteza.

Prioridade é relativa. Se muitos itens parecem igualmente altos, compare-os e
registre a ordem. Infraestrutura ou autorização podem preceder melhorias
visuais quando habilitam ou protegem outras entregas.

## Diagnóstico de prontidão

Antes de afirmar que um item está refinado, confirme:

- problema e pessoa beneficiada;
- evento que inicia o comportamento e resultado produzido;
- ator autorizado;
- regras, erros e exceções;
- verificação objetiva;
- implicações de segurança, privacidade e desempenho;
- fora de escopo;
- dependências e decisões pendentes.

O agente pergunta sobre lacunas materiais uma por vez. Uma decisão que muda
segurança, escopo, arquitetura ou experiência nunca é inventada silenciosamente.
Prontidão no backlog indica que o item pode seguir para especificação;
não autoriza implementação sem spec e gates.
