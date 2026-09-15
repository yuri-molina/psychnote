---
type: Index
title: Base de Conhecimento — psychnote-mfe
description: Catálogo principal e hub de navegação da base OKF do microfrontend de triagem clínica Psych Note.
timestamp: 2026-08-09T01:00:00-03:00
status: active
version: 3.2.0
owner: psychnote-mfe
---

# Base de Conhecimento — psychnote-mfe

Este diretório é a base de conhecimento descritiva (OKF) do `psychnote-mfe`, parte da arquitetura `MFE -> BFF -> Core` do projeto Psych Note. Documenta a aplicação com a nova tela inicial (`LandingView`), cadastro de novos pacientes com evolução (`NewPatientEvolutionView`), listagem de prontuários (`PatientListView`), triagem assíncrona orientada a eventos (HTTP 202 + SSE Stream), decisões e procedimentos operacionais.

Especificações de componentes, views e estados (SDD) são co-localizadas com o código-fonte em `src/`. Consulte o catálogo de specs abaixo para localizar cada artefato.

## Guia de Navegação para Agentes de IA

- Para entender termos clínicos ou técnicos, leia [`glossary.md`](./glossary.md).
- Para compreender a arquitetura geral do sistema, leia [`architecture/overview.md`](./architecture/overview.md).
- Para compreender a hierarquia de componentes e mapa de rotas, leia [`architecture/component-tree.md`](./architecture/component-tree.md).
- Para configurar ou modificar Module Federation, consulte [`architecture/module-federation.md`](./architecture/module-federation.md).
- Para implementar um componente React, leia o `.spec.md` co-localizado em `src/components/[name]/`.
- Para implementar uma view, leia o `.spec.md` co-localizado em `src/views/`.
- Para entender o fluxo de estados da triagem assíncrona, leia `src/hooks/useTriage.spec.md`.
- Para fazer chamadas HTTP e streaming SSE, consulte [`contracts/`](./contracts/).
- Para compreender as regras de domínio clínico, leia [`domain/clinical-triage.md`](./domain/clinical-triage.md).
- Para configurar o ambiente de desenvolvimento, siga [`playbooks/project-setup.md`](./playbooks/project-setup.md).
- Para entender decisões técnicas, leia os arquivos em [`decisions/`](./decisions/).
- Consulte [`log.md`](./log.md) para verificar alterações recentes.

## Catálogo OKF

### Raiz

| Caminho | Tipo | Descrição |
| :--- | :--- | :--- |
| [`glossary.md`](./glossary.md) | `Glossary` | Dicionário de termos clínicos e técnicos do projeto. |

### Arquitetura

| Caminho | Tipo | Descrição |
| :--- | :--- | :--- |
| [`architecture/overview.md`](./architecture/overview.md) | `Architecture` | Diagrama C4, stack tecnológica, mapa de rotas e fluxo assíncrono com SSE. |
| [`architecture/module-federation.md`](./architecture/module-federation.md) | `Architecture` | Configuração standalone-first com vite-plugin-federation. |
| [`architecture/folder-structure.md`](./architecture/folder-structure.md) | `Architecture` | Estrutura do src/, convenções de nomenclatura e regras de colocação. |
| [`architecture/component-tree.md`](./architecture/component-tree.md) | `Architecture` | Hierarquia de componentes, responsabilidades por view e regras de composição. |

### Decisões Arquiteturais (ADRs)

| Caminho | Tipo | Descrição |
| :--- | :--- | :--- |
| [`decisions/0001-standalone-first.md`](./decisions/0001-standalone-first.md) | `Decision` | Estratégia de desenvolvimento standalone-first. |
| [`decisions/0002-vite-plugin-federation.md`](./decisions/0002-vite-plugin-federation.md) | `Decision` | Escolha do @originjs/vite-plugin-federation. |
| [`decisions/0003-tailwind-css-isolation.md`](./decisions/0003-tailwind-css-isolation.md) | `Decision` | Isolamento de CSS com prefixo psy-. |
| [`decisions/0004-zod-runtime-validation.md`](./decisions/0004-zod-runtime-validation.md) | `Decision` | Validação de contratos de API com Zod. |
| [`decisions/0005-async-sse-triage.md`](./decisions/0005-async-sse-triage.md) | `Decision` | Arquitetura assíncrona de triagem com EventSource (SSE Stream) no MFE. |

### Contratos de API

| Caminho | Tipo | Descrição |
| :--- | :--- | :--- |
| [`contracts/core-api.md`](./contracts/core-api.md) | `Contract` | Contrato da API psychnote-core (FastAPI assíncrono + Webhook + ChromaDB). |
| [`contracts/bff-api.md`](./contracts/bff-api.md) | `Contract` | Contrato do BFF (HTTP 202 + EventSource SSE stream). |
| [`contracts/triage-job-status-spec.md`](./contracts/triage-job-status-spec.md) | `Contract` | Requisitos de desenvolvimento para BFF e Core (Status de Job e Prontuário com Triagem em Andamento). |

### Modelo de Domínio

| Caminho | Tipo | Descrição |
| :--- | :--- | :--- |
| [`domain/clinical-triage.md`](./domain/clinical-triage.md) | `DomainModel` | Regras clínicas, RiskLevel, auditoria de conduta e regras visuais. |

## Catálogo de Specs SDD (co-localizadas em src/)

### Views

| Caminho no Repositório | Tipo | Descrição |
| :--- | :--- | :--- |
| `src/views/LandingView.spec.md` | `LayoutSpec` | Composição da tela inicial (Landing View com CTAs principais). |
| `src/views/NewPatientEvolutionView.spec.md` | `LayoutSpec` | Composição da tela de cadastro de novo paciente e evolução clínica. |
| `src/views/PatientListView.spec.md` | `LayoutSpec` | Composição da tela de listagem de pacientes. |
| `src/views/PatientRecordView.spec.md` | `LayoutSpec` | Composição da tela de prontuário histórico do paciente. |
| `src/views/TriageLayout.spec.md` | `LayoutSpec` | Composição das telas de formulário e resultado de triagem. |
