---
type: Glossary
title: Dicionário de Termos — psychnote-bff
description: Termos ubíquos do domínio clínico e técnico usados no projeto PsicRE-AI e no psychnote-bff.
timestamp: 2026-08-07T16:55:00-03:00
status: active
version: 1.0.0
related:
  - ./domain/clinical-triage.md
---

# Dicionário de Termos — psychnote-bff

---

## Domínio Clínico

**Triagem de Risco**
Processo estruturado de avaliação inicial do risco suicida de um paciente com base em nota clínica em linguagem natural. Resultado principal do pipeline de IA do psychnote-core.

**Nota Clínica**
Texto em linguagem natural produzido pelo psicólogo durante ou após uma sessão, descrevendo o estado do paciente, queixas, comportamentos observados e evolução terapêutica. É o input primário do pipeline de IA.

**Nível de Risco**
Classificação ordinal do risco suicida inferida pelo Core a partir da nota clínica. Valores possíveis: `baixo`, `moderado`, `alto`, `crítico`.

**Red Flags**
Indicadores clínicos de alta gravidade identificados pelo pipeline de IA na nota clínica. Exemplos: menção a plano concreto, acesso a meios letais, histórico de tentativas anteriores.

**Fatores de Proteção**
Elementos identificados na nota clínica que reduzem o risco suicida. Exemplos: suporte familiar, vínculo terapêutico sólido, projetos de vida ativos.

**Ideação Passiva**
Pensamentos recorrentes sobre morte ou desejo de morrer sem elaboração de plano ou intenção. Classificada como risco moderado na maioria dos frameworks clínicos.

**Ideação Ativa**
Pensamentos sobre suicídio acompanhados de plano, intenção ou preparação. Classifica o caso como risco alto ou crítico.

**Auditoria de Conduta**
Registro imutável e rastreável das ações do psicólogo sobre um caso clínico, incluindo visualizações de triagem, anotações e encaminhamentos. Obrigatório por compliance ético e LGPD.

**Parecer Executivo**
Síntese gerada pelo pipeline de IA contendo: nível de risco, justificativa clínica, red flags identificados, fatores de proteção e recomendação de conduta. Compõe o payload de resposta do endpoint `POST /triage`.

**LGPD**
Lei Geral de Proteção de Dados (Lei nº 13.709/2018). Regula o tratamento de dados pessoais sensíveis, categoria que inclui dados de saúde mental. Toda persistência, transmissão e exibição de notas clínicas e triagens deve ser conforme à LGPD.

---

## Domínio Técnico

**BFF (Backend for Frontend)**
Serviço intermediário exclusivo entre o psychnote-mfe e o psychnote-core. Responsabilidades: rotear requisições HTTP, configurar CORS e Helmet, validar contratos de entrada e saída com Zod, gerenciar timeouts e transformar falhas do Core em respostas HTTP padronizadas. URL em desenvolvimento: `http://localhost:4000`.

**MFE**
O repositório `psychnote-mfe`. Único consumidor autorizado do BFF. Aplicação React + Vite executada na porta `5001` em ambiente de desenvolvimento.

**Core**
O repositório `psychnote-core`. API FastAPI + LangGraph responsável pela execução do pipeline de IA de triagem clínica. URL em desenvolvimento: `http://localhost:8000`. Latência esperada por requisição de triagem: 30–45 segundos.

**Fastify**
Framework HTTP Node.js de alta performance utilizado no BFF. Oferece suporte nativo a validação de schema via JSON Schema, sistema de plugins encapsulados e hooks de ciclo de vida de requisição. Alternativa ao Express com melhor throughput e tipagem via TypeScript.

**fastify-type-provider-zod**
Plugin que integra Zod como provider de tipagem e validação de schemas no Fastify, habilitando validação de request body, querystring, params e response schema diretamente nas definições de rota. Elimina a necessidade de conversão manual entre Zod e JSON Schema.

**@fastify/cors**
Plugin oficial do Fastify para configuração de Cross-Origin Resource Sharing (CORS). Obrigatório para permitir que o MFE (origem `http://localhost:5001`) realize requisições ao BFF. Configurado para restringir origens permitidas a valores explicitamente listados.

**@fastify/helmet**
Plugin oficial do Fastify para configuração de HTTP Security Headers via Helmet. Define cabeçalhos como `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options` e outros. Obrigatório para hardening de segurança do serviço.

**HTTP 202 Accepted**
Código de status HTTP que indica que a requisição de triagem foi aceita para processamento assíncrono, mas o processamento ainda não foi concluído. Retornado imediatamente pelo BFF e pelo Core acompanhado do `job_id`.

**Job ID (UUIDv4)**
Identificador único universal gerado pelo BFF no formato UUIDv4 para cada submissão de triagem clínica. Utilizado para rastrear o fluxo assíncrono entre MFE, BFF, Core e ChromaDB, correlacionando o canal SSE e a notificação de Webhook.

**SSE (Server-Sent Events)**
Tecnologia baseada em HTTP padrão (`text/event-stream`) que permite ao servidor enviar eventos unidirrecionais e atualizações em tempo real para o cliente (MFE) sem a necessidade de polling constante ou protocolo WebSocket.

**EventSource**
API nativa do navegador (HTML5) utilizada no MFE para estabelecer e gerenciar a conexão SSE contínua com o BFF no endpoint `GET /api/triage/stream/:jobId`, com suporte a reconexão automática.

**Webhook Callback**
Mecanismo de comunicação assíncrona HTTP `POST` utilizado pelo `psychnote-core` para notificar o `psychnote-bff` na rota `/api/webhooks/triage-result` assim que a execução do LangGraph e a persistência no ChromaDB são finalizadas.

**Active Connection Map (`activeSseConnections`)**
Estrutura de dados em memória no BFF (`Map<string, FastifyReply>`) responsável por mapear cada `job_id` ativo ao seu respectivo canal de resposta SSE aberto com o MFE.

**Heartbeat**
Mensagem de comentários sem efeito colateral (ex: `: heartbeat\n\n`) enviada periodicamente (a cada 15 segundos) pelo BFF na conexão SSE para manter a conexão TCP ativa e evitar encerramento por timeout em proxies, firewalls ou navegadores.

**AbortController**
API nativa do Node.js 18+ (e da biblioteca Undici) para cancelamento de requisições HTTP com base em sinal de abort. Utilizado no BFF para implementar o timeout máximo nas chamadas ao Core, evitando que requisições travadas bloqueiem o event loop indefinidamente.

**Long-polling**
Padrão legado de requisição HTTP mantida aberta aguardando resposta do servidor. Foi substituído na plataforma PsicRE-AI pela arquitetura assíncrona baseada em HTTP 202 + Webhook + SSE Stream.

**502 Bad Gateway**
Código HTTP retornado pelo BFF quando o Core retorna resposta inválida, JSON malformado ou quando a resposta falha na validação do schema Zod do contrato de downstream. Indica falha no serviço de upstream.

**504 Gateway Timeout**
Código HTTP retornado pelo BFF quando uma chamada síncrona ultrapassa o limite de tempo aceitável.

**Payload Amigável de Erro**
Estrutura JSON padronizada retornada pelo BFF em todos os cenários de falha. Campos obrigatórios: `statusCode` (número HTTP), `error` (string com nome do erro), `message` (descrição legível por humanos), `upstream` (string identificando o serviço falho, ex: `"psychnote-core"`).

**Crash-free**
Premissa operacional que define que o processo Node.js do BFF nunca deve terminar de forma inesperada por erros de runtime oriundos de falhas do Core ou de qualquer serviço de upstream. Todos os erros de upstream devem ser interceptados pelo handler global e transformados em respostas HTTP estruturadas com payload amigável.

**Out-of-Scope**
Funcionalidades explicitamente fora do escopo do BFF: banco de dados próprio, renderização de views HTML, execução de inferência ou lógica de IA, gerenciamento de sessões de usuário e autenticação de identidade.

