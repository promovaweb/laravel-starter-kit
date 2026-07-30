# Projeto

## História e motivação

O projeto parte do Laravel React Starter Kit e evolui essa base para reunir,
em um único ponto de partida, capacidades recorrentes de aplicações web
modernas. Além da autenticação fornecida pelo ecossistema Laravel, o repositório
incorpora segurança de conta, equipes, associação de usuários, convites e
controle de acesso por papéis.

A motivação é reduzir o trabalho repetitivo necessário para iniciar aplicações
Laravel com uma experiência integrada entre backend e frontend, mantendo uma
base pequena, verificável por testes e pronta para receber regras de negócio
específicas.

## Finalidade

Fornecer uma fundação reutilizável para aplicações web Laravel que precisam de
autenticação, gerenciamento seguro de contas e colaboração organizada por
equipes. O resultado esperado é permitir que novos produtos comecem a partir de
fluxos transversais já implementados, para que o desenvolvimento possa se
concentrar no domínio próprio de cada aplicação.

## Pessoas e contexto de uso

- Pessoas desenvolvedoras usam o repositório como base para iniciar e evoluir
  aplicações Laravel com frontend React.
- Pessoas usuárias das aplicações derivadas criam contas, autenticam-se,
  protegem suas credenciais e administram seu perfil.
- Membros de equipes alternam o contexto de trabalho, recebem convites e
  colaboram conforme o papel que possuem.
- Proprietários e administradores de equipes gerenciam dados da equipe,
  convites, membros e permissões.

## Capacidades principais

- Registro, login, recuperação de senha, verificação de e-mail e confirmação de
  senha.
- Proteção de conta com autenticação de dois fatores e passkeys.
- Atualização de perfil, senha, preferências de aparência e exclusão da conta.
- Criação de equipe pessoal e de equipes adicionais.
- Alternância entre equipes e isolamento do acesso pelo vínculo de associação.
- Convites por e-mail com expiração, aceite, recusa e cancelamento.
- Gestão de membros, papéis e permissões de equipe.
- Base de dashboard e componentes de interface pronta para extensão.
- Qualidade automatizada com testes, análise estática, lint, formatação e
  verificação de tipos.

## Limites

- Não representa um produto de negócio final nem define um domínio comercial
  específico.
- Não fornece conteúdo funcional para o dashboard além da estrutura inicial e
  dos convites pendentes.
- Não substitui as regras de autorização próprias que cada aplicação derivada
  precisar adicionar ao seu domínio.
- Não assume infraestrutura de produção, estratégia de implantação, provedor
  de e-mail ou banco de dados de produção.
- Não oferece, na base atual, uma API pública versionada nem clientes móveis.

## Contexto técnico

Aplicação web monolítica baseada em Laravel, com respostas Inertia e interface
React. O backend concentra autenticação, autorização, persistência e fluxos de
equipes; o frontend concentra páginas, formulários, navegação e feedback de
interação.

As fronteiras HTTP são declaradas nas rotas web e de configurações. Os módulos
persistentes centrais são usuários, credenciais, equipes, associações e
convites, acompanhados pelas estruturas operacionais do Laravel para sessões,
cache e filas. O console sustenta tarefas operacionais do framework, incluindo
a remoção periódica de convites expirados.

As tecnologias estruturais e suas evidências ficam em `.specsfy/STACK.md`. O
mapa verificável de persistência fica em `.specsfy/DATABASE.md`.
