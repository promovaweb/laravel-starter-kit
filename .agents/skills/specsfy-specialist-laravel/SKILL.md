---
name: specsfy-specialist-laravel
description: Implementar, revisar e operar aplicações Laravel — HTTP, Eloquent, autorização, filas, eventos, cache e testes. Use quando o projeto contém `artisan` ou `laravel/framework` e a tarefa toca rotas, controllers, models, policies, jobs, commands, migrations, Pest ou PHPUnit; não use para PHP sem Laravel nem para modelagem de Postgres em si — combine com `specsfy-specialist-postgres` quando a decisão for de schema ou índice.
---

# Laravel

## Quando usar

- Acionar quando o repositório tem `artisan`, `composer.json` com
  `laravel/framework`, e a tarefa envolve rotas, controllers, models,
  policies, form requests, jobs, eventos, cache, config ou testes Laravel.
- Acionar também para revisão de PR Laravel, diagnóstico de N+1, fila
  travada, autorização quebrada ou migration arriscada.
- Não acionar para decisão pura de schema, índice ou plano de query — usar
  `$specsfy-specialist-postgres` e trazer o resultado para o Eloquent.
- Combinar com `$specsfy-specialist-application-security` quando a mudança
  tocar autenticação, mass assignment, upload ou dado sensível, e com
  `$specsfy-specialist-supabase` quando o Postgres for gerenciado por
  Supabase em vez de instância própria.

## Fluxo

1. Ler `composer.json`/`composer.lock` para confirmar versão do framework,
   PHP e pacotes relevantes (Sanctum, Horizon, Octane, Scout) antes de supor
   comportamento por memória.
2. Mapear a requisição do ponto de entrada até domínio, persistência,
   efeitos assíncronos e resposta, identificando o boundary onde a regra de
   negócio já vive no projeto (Action, Service, Model rico).
3. Localizar convenções irmãs — como o projeto organiza Form Requests,
   Policies, Resources e Jobs — e seguir o padrão existente em vez de
   introduzir um novo.
4. Definir autorização, validação, transação, idempotência e modo de falha
   antes de escrever código, especialmente para jobs e webhooks.
5. Escrever o teste focal (Pest ou PHPUnit conforme o projeto), implementar a
   menor fatia que o torna verde e então refatorar.
6. Inspecionar as queries geradas (`DB::listen`, Telescope, Debugbar ou
   `EXPLAIN` via `$specsfy-specialist-postgres`) quando cardinalidade ou
   latência importarem.
7. Executar testes, análise estática (Larastan/PHPStan) e formatter (Pint)
   disponíveis no projeto antes de considerar a tarefa concluída.
8. Verificar impacto operacional — migration em produção, workers, scheduler,
   cache de config — e registrar risco quando a ação exigir autorização
   externa.

## Padrões

- Manter controllers finos: validação em Form Requests, autorização em
  Policies/Gates, regra de negócio no boundary já adotado pelo projeto.
- Tratar Eloquent como acesso a dados: eager load explícito (`with`,
  `withCount`) sempre que uma coleção acessar relação em loop; nunca escrever
  N+1 e justificar "está rápido o bastante por enquanto".
- Selecionar colunas (`select`) quando a tabela for larga ou a listagem não
  precisar do model completo; preferir `chunkById`/`lazyById` para varreduras
  grandes em vez de carregar tudo em memória.
- Projetar jobs idempotentes: `ShouldBeUnique`/lock quando duplicidade for
  possível, timeout e tentativas explícitos, `failed()` tratando o efeito
  colateral de falha definitiva.
- Migrations compatíveis com o volume real: `expand → migrar dado → contract`
  para mudança incompatível em tabela grande; nunca um único `ALTER` bloqueante
  sem medir o lock esperado.
- Nunca confiar em validação do cliente nem autorizar somente na UI —
  Policy/Gate roda no servidor em toda ação e em todo objeto, não só na rota
  de criação.
- Proteger mass assignment com `$fillable` (ou `$guarded` deliberado) e nunca
  passar `$request->all()` direto para `create`/`update` sem validação prévia.
- Não criar abstração, evento, pacote ou camada extra sem um segundo
  consumidor real e benefício verificável — três controllers parecidos não
  justificam um framework interno.

## Antipadrões

- Model "gordo" que mistura regra de negócio, efeito colateral externo e
  apresentação no mesmo método — sintoma de que o boundary do projeto não foi
  seguido.
- Policy que autoriza pela presença do usuário autenticado, sem checar
  ownership do objeto — abre acesso cross-tenant mesmo com `auth` middleware
  presente.
- Job que reprocessa efeito não idempotente (enviar e-mail, cobrar cartão) sem
  chave de deduplicação — reentrega do worker duplica o efeito.
- Migration com `Schema::table` renomeando ou removendo coluna usada em
  produção no mesmo deploy que o código que a lê — quebra a janela de deploy
  misto.
- Teste que usa `RefreshDatabase` mas não recria os dados mínimos de
  autorização, mascarando policy ausente com um usuário "admin" fixo.

## Validação

- Cobrir caminho feliz, autorização negada, validação, efeitos colaterais e
  falhas relevantes (job falho, dependência externa indisponível).
- Rodar a suíte com `RefreshDatabase`/factories e confirmar que o teste falha
  sem a mudança (RED) antes de implementar.
- Inspecionar queries geradas quando a tela lista uma coleção com relação —
  contar queries antes/depois (`assertQueryCountLessThan`, Debugbar, log de
  queries) para provar ausência de N+1.
- Verificar queues, scheduler, cache de config/rotas e variáveis de ambiente
  no ambiente alvo antes de declarar a tarefa pronta para deploy.
- Não declarar "seguro" ou "idempotente" sem teste que exercite o cenário
  adversarial correspondente (replay do job, payload malformado, usuário sem
  permissão).

## Skills relacionadas

- `$specsfy-specialist-postgres` para modelagem de schema, índice e plano de
  query por trás do Eloquent.
- `$specsfy-specialist-supabase` quando o Postgres do projeto for gerenciado
  por Supabase (RLS substitui parte da autorização de aplicação).
- `$specsfy-specialist-application-security` para autenticação, mass
  assignment, upload e trilha de auditoria.
- `$specsfy-specialist-redis` quando cache, fila ou lock usar Redis como
  driver.
- `$specsfy-specialist-docker`/`$specsfy-specialist-docker-swarm` para
  empacotar e operar a aplicação em produção.

Leia [references/standards.md](references/standards.md) para checklist por
superfície (HTTP, domínio, Eloquent, filas, dados, segurança, operação) e
fontes oficiais da versão instalada.
