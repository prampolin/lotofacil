# P11 — Segurança, performance e estabilidade

Data: 2026-10-10 (America/Sao_Paulo). **Concluído para continuidade local do backend. Não liberado para produção.** P12 não possui especificação neste repositório; há base técnica para iniciar a próxima etapa de desenvolvimento, mas um P12 de publicação depende dos requisitos operacionais abaixo.

## Escopo e evidências

AGENTS.md, plan.md, SPEC-00–11, README e relatórios P09/P10/P10.1 revisados. Mudanças preexistentes preservadas. PostgreSQL de desenvolvimento acessado somente para snapshot e verificação em transação READ ONLY. Testes e fixtures de performance exclusivamente no banco `test_lotofacil`, com bloqueio global de HTTP requests e Caixa mockada. Nenhuma importação real, deploy, mudança de concurso/log real, migration ou exclusão de volume executada.

Arquivos de evidência em [p11/](p11/): `baseline-tests.log`, `focused.log`, `security-regression.log`, `tests.log` (intermediário), `gates.log` (final), `performance.log`, `before.json` e `database-verification.json`. Logs intermediários contêm falhas de desenvolvimento corrigidas; o resultado final está em gates.log.

## Achados e correções

| Severidade inicial | Achado | Correção / evidência |
| --- | --- | --- |
| Alta | SECRET_KEY e senha PostgreSQL literais no settings/compose; bytecode de settings versionado também continha os valores | Configuração via ambiente, SECRET_KEY obrigatória; compose exige POSTGRES_PASSWORD. Bytecode de settings removido da árvore de trabalho; `.gitignore` protege .env, caches e venvs. Busca dos valores legados nos arquivos rastreados atuais da aplicação não encontrou ocorrências. Histórico Git continua contaminado: ver pendências. |
| Alta | DEBUG=True e ausência de perfil seguro para produção | DEBUG=false por padrão; hosts locais explícitos no perfil base. `config.production` força DEBUG=false e recusa chave ausente/fraca, hosts vazios/wildcards e senha ausente; cookies Secure, HTTPS redirect, HSTS e SMTP/TLS com timeout. Check --deploy sem warnings. |
| Média | Sem limite pequeno de corpo antes do parsing da API | Middleware restringe leitura a 64 KiB + 1 byte; excesso retorna 413 JSON antes dos serviços, inclusive sem Content-Length na requisição testada. Corpo pequeno e contratos anteriores passam na suíte. |
| Alta | Importadores concorrentes podiam consultar/gravar o mesmo intervalo | Advisory lock de sessão PostgreSQL compartilhado pelos três comandos, reentrante nas chamadas internas. Testes usam outra conexão/thread: concorrente recebe CommandError antes de HTTP; liberação e nova aquisição após erro verificadas. Nenhuma migration necessária. |
| Média | Ctrl-C deixava SyncExecution running | KeyboardInterrupt dentro do processamento registra failed, finished_at e causa, preserva progresso e propaga interrupção. Regressão confirma retomada somente do concurso ausente. SIGKILL continua uma limitação. |
| Média | sync materializava lista completa de lacunas antes de aplicar limit | Contagem aritmética e seleção preguiçosa via islice; valida latest no domínio de inteiro do modelo. Regressão com latest=2147483647 seleciona apenas 25 sem alocar bilhões de entradas; somente mock/dry-run. |
| Baixa | Gerador recalculava tabela combinatória invariável a cada chamada | Cache de uma entrada, frozenset imutável; teste confirma uma construção, reutilização, mesma resposta/seed. Nenhuma alteração no RNG ou algoritmo de amostragem. |

O primeiro check do perfil de produção detectou `mail.E001` (backend de console). Corrigido para SMTP com TLS e timeout 10s; nenhuma conexão/envio de e-mail foi feito. O servidor SMTP real e a entrega ainda precisam ser configurados e verificados antes de uso operacional.

Não foram adicionadas dependências, índices ou migrations. Contratos de sucesso, campos JSON, caminhos e CLI mantidos; nova resposta 413 para excesso de corpo documentada em SPEC-08/README. Os testes dos comandos agora autorizam acesso ao banco isolado também nos casos de erro HTTP, pois a exclusão mútua exige conexão antes da rede.

## Segurança revisada

- API segue pública com AllowAny explícito; admin continua exigindo login e sem edição dos dados. Autenticação obrigatória não foi introduzida. SessionAuthentication/CSRF existentes preservados.
- CORS não habilitado; origem externa não recebe Access-Control-Allow-Origin. Isso restringe leitura pelo navegador, não impede clientes diretos nem substitui autorização.
- Hosts inesperados retornam 400; erros internos com DEBUG=false não expõem traceback nem mensagem privada na resposta (500 genérico). Logs do servidor podem conter detalhes e precisam de acesso restrito/retenção.
- JSON estrito, campos desconhecidos, booleanos/floats, limites numéricos, métodos, JSON malformado e profundidade excessiva verificados. Geração até 100 jogos/10000 tentativas, estatísticas até 1000 registros, backtest até 200 × 100 permanecem limitados.
- Limite de corpo não limita taxa ou concorrência de requisições. Não há rate limiting distribuído nem teste de abuso na borda; configurar proxy/gateway antes de exposição pública. Throttling DRF isolado não é proteção contra DoS, conforme a [documentação oficial](https://www.django-rest-framework.org/api-guide/throttling/).
- Perfil seguro segue a [checklist oficial Django](https://docs.djangoproject.com/en/dev/howto/deployment/checklist/). Passar check --deploy não valida infraestrutura, TLS, proxies, backups ou segredos históricos.

## Performance local observada

Fixture: 4000 concursos sintéticos, 3 requisições sequenciais por cenário pelo APIClient (middleware, ORM e renderização JSON), sem servidor TCP. Mediana/máximo incluem overhead de instrumentação SQL e possíveis aquecimentos. Não são p95/p99, SLA ou benchmark de tráfego concorrente. Sem carga em serviços externos.

| Cenário | Mediana ms | Máximo ms | SQL por request | Bytes resposta | HTTP |
| --- | ---: | ---: | ---: | ---: | ---: |
| statistics_1 | 0.754 | 9.287 | 1 | 2189 | 200 |
| statistics_100 | 1.560 | 1.597 | 1 | 12721 | 200 |
| statistics_1000 | 9.293 | 10.040 | 1 | 108140 | 200 |
| generate_100 | 0.656 | 5.108 | 0 | 4281 | 200 |
| generate_rare | 30.719 | 31.068 | 0 | 92 | 400 |
| backtest_10x10 | 1.876 | 2.265 | 1 | 5733 | 200 |
| backtest_200x100 | 82.840 | 94.807 | 1 | 936446 | 200 |

Filtro raro: 100 jogos com soma exatamente 120; esgota o limite de 10000 tentativas e retorna 400 em tempo limitado. Não foi alterado o contrato para prometer sucesso em filtros raros. Geração de 100 jogos com cache frio: **5,918 ms**; reutilização com mesma seed: **0,309 ms**, respostas idênticas. São duas observações de serviço, não comparação estatística de versões.

Estatísticas e backtests usam uma consulta limitada (LIMIT 1000 e LIMIT 201 no teto); geração não acessa SQL. Latest/detail já têm uma consulta e testes continuam aprovados. EXPLAIN em fixture mostrou `Index Scan Backward using results_contest_number_key`; índice único existente atende seleção/ordenação. Custos/cardinalidades do planner são estimativas, não tempos reais; não houve necessidade de índice novo nem ANALYZE no banco real.

Gargalos restantes: JSON de backtest no teto com **936446 bytes**, geração aleatória de até 20000 jogos e cálculo duplicado de hits no rolling. Mantidos para preservar contrato, com custo local limitado. Não medidos: RSS/pico de memória, CPU sob concorrência HTTP, servidor WSGI/ASGI, rede/proxy ou hardware de produção.

## Resiliência e recuperação

- Timeout HTTP existente de 20s e até três tentativas de detalhe em timeout/conexão, 429 e 5xx; backoff max(delay, 2s/4s), delay mínimo existente respeitado. Erros permanentes não repetem; regressões anteriores seguem passando.
- Retry-After ainda não é interpretado; 429 ainda usa o retry legado. Não existe loop de lotes automático. O operador deve interromper diante de bloqueio observado e só retomar com autorização. O invólucro especial P10.1 não foi transformado em mudança silenciosa do contrato 429.
- Consulta latest continua antes da criação de SyncExecution e sem retry; falha nela aparece no terminal, não em um novo log no banco. Capturar stdout/stderr no executor operacional continua necessário.
- Locks protegem os três comandos cooperantes conectados ao mesmo banco; save_contest/SQL externo podem ignorá-los. Requer conexão direta ou pool de sessão. **Não usar pooling de transação para importadores.**
- Perda de conexão/rollback libera lock ao fechar sessão; erro de liberação não substitui exceção original. Salvamento de concurso e progresso ainda são operações separadas. Banco indisponível pode impedir log final.
- SIGKILL, SIGTERM padrão ou queda da máquina podem deixar running. Após confirmar que o processo terminou e que não há outro operador, inspecionar log e concursos já persistidos. A próxima execução autorizada seleciona ausentes; não confia em processed para decidir importação. Logs antigos não são automaticamente reclassificados nem apagados. Não se simularam SIGKILL/processo morto em produção.

## Gates e preservação

| Comando | Resultado final | Exit |
| --- | --- | ---: |
| ruff check . | All checks passed! | 0 |
| ruff format --check . | 44 files already formatted | 0 |
| python manage.py check | 0 issues | 0 |
| python manage.py check --deploy --settings=config.production --fail-level=WARNING | 0 issues; host de teste explícito, sem deploy | 0 |
| python -m pytest -q | **136 passed in 3.13s** | 0 |
| python manage.py makemigrations --check --dry-run | No changes detected | 0 |
| python manage.py migrate --check | Sem saída; nenhuma migration aplicada | 0 |

Baseline sem permissão TCP: 71 passed, 47 errors, 1 warning (4.11s); repetição autorizada **118 passed in 2.01s**. Foram adicionados 18 casos. Focado intermediário: 42 passed/1 failed (SMTP de produção); outro intermediário: 8 passed/3 failed por erro de import introduzido na edição e corrigido. Verificação completa posterior: 133 passed; final após casos adicionais de hosts: 136 passed. Lint intermediário apontou imports incorretos, resolvidos; nenhum gate pendente foi tratado como aprovado.

Verificação final READ ONLY: **266 concursos e 2 SyncExecution**, todos os campos iguais ao snapshot inicial; validação de todos os concursos sem erros. SHA-256 do snapshot combinado: `38768cb313e1f9925710b66402b155feb445cec6a46efcf6f94ca40d93dce308`. Nenhuma escrita destrutiva ou mudança de dados reais. Migrations existentes intactas.

## Configuração e riscos para P12

1. Carregar `backend/.env` no shell (`set -a; source .env; set +a`), conforme README. Foi criada uma nova chave local privada e mantida a senha atual do banco no arquivo ignorado, modo 0600. A chave nova invalida assinaturas/sessões antigas; pode ser necessário novo login. Não se alterou senha/role no PostgreSQL.
2. **Credenciais antigas continuam no histórico Git e no HEAD até o commit da correção.** Não é possível afirmar que nunca foram versionadas. Não houve commit, reescrita do histórico ou rotação do banco. Antes de produção: segredos novos exclusivos, rotação coordenada de qualquer valor reutilizado e avaliação da limpeza do histórico. A varredura foi direcionada aos valores legados no código da aplicação; não foi um scanner exaustivo de todos os commits/dependências. Outros bytecodes/venv anteriormente rastreados continuam como dívida de higiene Git; ignorar não os remove retroativamente.
3. Configurar e validar HTTPS, proxy confiável, limites de corpo/taxa/timeout na borda e servidor de aplicação. SECURE_PROXY_SSL_HEADER permanece desativado: não confiar em cabeçalhos arbitrários. Se TLS terminar no proxy, estabelecer confiança corretamente para evitar redirects em loop. HSTS de um ano/includeSubDomains/preload exige HTTPS em todos os subdomínios antes de ativar este perfil em um domínio real; nenhuma inscrição em preload foi efetuada.
4. Definir privilégios mínimos do usuário PostgreSQL de produção, backups/restauração, monitoração e alertas, persistência/rotação de logs e política de recuperação de execuções interrompidas. O usuário local de testes precisa criar seu banco isolado; não deve ser copiado como role de produção.
5. Não realizada auditoria CVE transitiva completa, instalação limpa ou validação de deployment. Dependências não foram atualizadas sem evidência de necessidade.

**Decisão:** backend apto a continuar P12 em desenvolvimento local. Publicação não aprovada: itens operacionais e tratamento dos segredos históricos continuam pendentes. Nenhuma importação adicional autorizada ou realizada.

Revisão final: `git diff --check` exit 0; fontes novas também inspecionadas diretamente. Alterações P11 em settings/compose, novos production/middleware/import_lock, três comandos, cache do gerador, testes de segurança/performance e marcadores de banco nos testes de comandos; README, SPEC-08, plan.md e este relatório atualizados. Nenhum commit realizado.
