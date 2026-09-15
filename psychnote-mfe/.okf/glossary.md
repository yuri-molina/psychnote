---
type: Glossary
title: Dicionário de Termos — psychnote-mfe
description: Termos ubíquos do domínio clínico e técnico usados no projeto PsicRE-AI e no psychnote-mfe.
timestamp: 2026-08-07T12:00:00-03:00
status: active
version: 1.0.0
related:
  - ./domain/clinical-triage.md
---

# Dicionário de Termos

## Domínio Clínico

**Triagem de Risco**
Processo de avaliação estruturada de uma nota clínica para classificar o nível de risco de suicídio do paciente. Executada pelo pipeline LangGraph no psychnote-core.

**Nota Clínica (current_note)**
Texto livre descritivo redigido pelo profissional de saúde durante ou após a consulta com o paciente. É o insumo primário do pipeline de triagem.

**Nível de Risco (risk_level)**
Classificação discreta em três categorias: `Baixo`, `Moderado` ou `Alto/Iminente`. Ver regras completas em [`domain/clinical-triage.md`](./domain/clinical-triage.md).

**Red Flags**
Fragmentos textuais ou comportamentos extraídos da nota clínica que configuram fatores de risco agudo. Exemplos: carta de despedida, data definida, acesso a meios letais.

**Fatores de Proteção (protection_factors)**
Elementos identificados na nota que mitigam o risco: rede de apoio familiar, aliança terapêutica, religiosidade, planos futuros concretos.

**Ideação Passiva (passive_ideation)**
Pensamentos de morte sem planejamento ativo. Exemplos linguísticos: "queria descansar para sempre", "não quero mais estar aqui".

**Ideação Ativa (active_ideation)**
Planejamento tático de suicídio, com método, local ou data definidos. Configura risco Alto/Iminente.

**Auditoria de Conduta (audit_conduct)**
Nó 3 do pipeline LangGraph. Compara o nível de risco classificado com a conduta médica narrada na nota e gera alertas de desvio de protocolo clínico.

**Parecer Executivo (final_report)**
Texto consolidado gerado pelo Nó 4 do LangGraph, sintetizando a avaliação de risco, os alertas de auditoria e a justificativa clínica.

**LGPD**
Lei Geral de Proteção de Dados (Lei 13.709/2018). Premissa não negociável do projeto: nenhum dado de paciente pode transitar fora do ambiente local (Edge AI).

## Domínio Técnico

**MFE (Microfrontend)**
O repositório `psychnote-mfe`. Aplicação React independente que compõe a camada de apresentação da arquitetura.

**BFF (Backend for Frontend)**
Serviço intermediário entre o MFE e o Core. Agrega, transforma e adapta os dados das Core APIs para o formato de consumo do MFE. Desenvolvido em paralelo por agente separado. URL esperada: `http://localhost:4000`.

**Core**
O repositório `psychnote-core`. API FastAPI que executa o pipeline de IA (LangGraph + Ollama + ChromaDB). URL: `http://localhost:8000`.

**Module Federation**
Mecanismo de compartilhamento de código em tempo de execução entre aplicações JavaScript. Permite que o MFE seja carregado dinamicamente por um Shell App (Host) sem recompilação. Implementado via `@originjs/vite-plugin-federation`.

**Remote (Module Federation)**
O papel do `psychnote-mfe` na arquitetura de Module Federation. Expõe o componente `PsychnoteMfe` via `remoteEntry.js`.

**Host / Shell App (Module Federation)**
Aplicação principal que consome e orquestra Remotes. Não existe ainda no escopo atual; o MFE é desenvolvido em modo standalone até a criação do Shell.

**Standalone-First**
Estratégia de desenvolvimento onde o MFE funciona como SPA completa e autônoma (`npm run dev`) durante o desenvolvimento, mas com Module Federation pré-configurado para integração futura com o Shell App.

**remoteEntry.js**
Arquivo de manifesto gerado pelo `vite build` do Remote. Contém os metadados e ponteiros para os módulos expostos. Consumido pelo Host em tempo de execução.

**Zod**
Biblioteca TypeScript de validação de schemas em runtime. Usada para validar os contratos de API do BFF antes de renderizar dados clínicos na UI.

**TanStack Query**
Biblioteca de gerenciamento de estado assíncrono (fetching, caching, mutations). Declarada como `singleton` no Module Federation para evitar múltiplas instâncias entre MFE e Shell App.

**Prefixo psy-**
Prefixo obrigatório em todas as classes utilitárias Tailwind CSS do MFE (ex: `psy-flex`, `psy-bg-primary`). Evita colisão de estilos quando o MFE é carregado pelo Shell App.
