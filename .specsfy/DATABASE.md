# Banco de dados

Mapa de persistência do sistema. Modelo inicial sugerido para
**Laravel**.

Para Laravel, descreva módulos de domínio, fronteiras HTTP/console e use `database/migrations` como primeira evidência do mapa de dados.

## Fontes de dados

<!-- specsfy:database:start -->
| Fonte | Tecnologia/forma | Evidência |
| --- | --- | --- |
| Principal | SQLite | `.env.example` (`DB_CONNECTION`) e schema ativo em `database/database.sqlite` |
| Estrutura | Schema/migration | `database/migrations/0001_01_01_000000_create_users_table.php` |
| Estrutura | Schema/migration | `database/migrations/0001_01_01_000001_create_cache_table.php` |
| Estrutura | Schema/migration | `database/migrations/0001_01_01_000002_create_jobs_table.php` |
| Estrutura | Schema/migration | `database/migrations/2024_01_01_000000_create_passkeys_table.php` |
| Estrutura | Schema/migration | `database/migrations/2025_08_14_170933_add_two_factor_columns_to_users_table.php` |
| Estrutura | Schema/migration | `database/migrations/2026_01_27_000001_create_teams_table.php` |
| Estrutura | Schema/migration | `database/migrations/2026_01_27_000002_add_current_team_id_to_users_table.php` |

## Estruturas detectadas

| Estrutura | Tipo | Campos | Relações, índices e constraints | Fonte |
| --- | --- | --- | --- | --- |
| migrations | Tabela de controle | id:integer, migration:varchar, batch:integer | PK(id) | Schema ativo do Laravel |
| users | Tabela | id:integer, name:varchar, email:varchar, email_verified_at:datetime?, password:varchar, remember_token:varchar?, created_at:datetime?, updated_at:datetime?, two_factor_secret:text?, two_factor_recovery_codes:text?, two_factor_confirmed_at:datetime?, current_team_id:integer? | PK(id); UNIQUE(email); FK current_team_id → teams.id, `SET NULL` ao excluir | `database/migrations/0001_01_01_000000_create_users_table.php`, `database/migrations/2025_08_14_170933_add_two_factor_columns_to_users_table.php`, `database/migrations/2026_01_27_000002_add_current_team_id_to_users_table.php` |
| password_reset_tokens | Tabela | email:varchar, token:varchar, created_at:datetime? | PK(email) | `database/migrations/0001_01_01_000000_create_users_table.php` |
| sessions | Tabela | id:varchar, user_id:integer?, ip_address:varchar?, user_agent:text?, payload:text, last_activity:integer | PK(id); INDEX(user_id); INDEX(last_activity); referência lógica user_id sem FK | `database/migrations/0001_01_01_000000_create_users_table.php` |
| cache | Tabela | key:varchar, value:text, expiration:integer | PK(key); INDEX(expiration) | `database/migrations/0001_01_01_000001_create_cache_table.php` |
| cache_locks | Tabela | key:varchar, owner:varchar, expiration:integer | PK(key); INDEX(expiration) | `database/migrations/0001_01_01_000001_create_cache_table.php` |
| jobs | Tabela | id:integer, queue:varchar, payload:text, attempts:integer, reserved_at:integer?, available_at:integer, created_at:integer | PK(id); INDEX(queue) | `database/migrations/0001_01_01_000002_create_jobs_table.php` |
| job_batches | Tabela | id:varchar, name:varchar, total_jobs:integer, pending_jobs:integer, failed_jobs:integer, failed_job_ids:text, options:text?, cancelled_at:integer?, created_at:integer, finished_at:integer? | PK(id) | `database/migrations/0001_01_01_000002_create_jobs_table.php` |
| failed_jobs | Tabela | id:integer, uuid:varchar, connection:varchar, queue:varchar, payload:text, exception:text, failed_at:datetime | PK(id); UNIQUE(uuid); INDEX(connection, queue, failed_at) | `database/migrations/0001_01_01_000002_create_jobs_table.php` |
| passkeys | Tabela | id:integer, user_id:integer, name:varchar, credential_id:varchar, credential:text, last_used_at:datetime?, created_at:datetime?, updated_at:datetime? | PK(id); UNIQUE(credential_id); INDEX(user_id); FK user_id → users.id, `CASCADE` ao excluir | `database/migrations/2024_01_01_000000_create_passkeys_table.php` |
| teams | Tabela | id:integer, name:varchar, slug:varchar, is_personal:boolean, created_at:datetime?, updated_at:datetime?, deleted_at:datetime? | PK(id); UNIQUE(slug); exclusão lógica por deleted_at | `database/migrations/2026_01_27_000001_create_teams_table.php` |
| team_members | Tabela pivô | id:integer, team_id:integer, user_id:integer, role:varchar, created_at:datetime?, updated_at:datetime? | PK(id); UNIQUE(team_id, user_id); FKs team_id → teams.id e user_id → users.id, ambas `CASCADE` ao excluir | `database/migrations/2026_01_27_000001_create_teams_table.php` |
| team_invitations | Tabela | id:integer, code:varchar, team_id:integer, email:varchar, role:varchar, invited_by:integer, expires_at:datetime?, accepted_at:datetime?, created_at:datetime?, updated_at:datetime? | PK(id); UNIQUE(code); FKs team_id → teams.id e invited_by → users.id, ambas `CASCADE` ao excluir | `database/migrations/2026_01_27_000001_create_teams_table.php` |
<!-- specsfy:database:end -->

## Decisões, ownership e retenção

Registre finalidade, ownership, classificação, retenção, constraints e decisões
que não estejam explícitas nos schemas.
