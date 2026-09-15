---
type: ComponentSpec
id: CS-PATIENT-CARD
title: Especificação de Componente — PatientCard
description: Card atômico de exibição e seleção de um paciente na listagem. Único dado disponível é o patient_id nesta versão da PoC.
timestamp: 2026-08-07T14:35:00-03:00
status: approved
version: 1.0.0
owner: psychnote-mfe
tags: [component, patient, card, atomic]
related:
  - ../../contracts/bff-api.md
  - ../layouts/patient-list-layout.md
  - ../../architecture/component-tree.md
---

# ComponentSpec: PatientCard

## 1. Visão Geral e Propósito

Representa um paciente na listagem. O único dado disponível nesta versão da PoC é o `patient_id`. Ao ser clicado ou ativado por teclado, aciona a seleção do paciente e navega para o formulário de triagem.

### Anti-patterns

- Não exibir dados de triagens anteriores neste componente. O card é apenas um ponto de entrada para a triagem individual.
- Não armazenar estado de seleção internamente. O estado de paciente selecionado pertence à view pai ou ao router.

## 2. Interface Pública (Props)

| Prop | Tipo | Obrigatório | Valor Padrão | Descrição |
| :--- | :--- | :---: | :---: | :--- |
| `patientId` | `string` | Sim | — | Identificador único do paciente (ex: "PAC-001"). |
| `onSelect` | `(patientId: string) => void` | Sim | — | Callback disparado ao clicar no card. Responsabilidade de navegação pertence à view. |
| `isSelected` | `boolean` | Não | `false` | Indica se este paciente está atualmente selecionado. Aplica variante visual de seleção. |

## 3. Variantes Visuais

| Estado | Descrição |
| :--- | :--- |
| Default | Card com borda sutil, fundo neutro |
| Hover | Fundo levemente elevado, cursor pointer |
| Selected (`isSelected=true`) | Borda de destaque na cor primária, fundo levemente colorido |
| Focus (teclado) | Outline visível conforme padrão do design system |

## 4. Requisitos de Acessibilidade (A11y)

- O card raiz é um elemento `<button>` ou `<div role="button">` com `tabIndex={0}`.
- Responde às teclas `Enter` e `Space` chamando `onSelect`.
- `aria-label`: `"Selecionar paciente [patientId]"`.
- `aria-pressed={isSelected}` quando em estado de seleção.

## 5. Casos de Borda

| Situação | Comportamento Esperado |
| :--- | :--- |
| `patientId` muito longo | Texto truncado com reticências (`text-ellipsis overflow-hidden`). Tooltip com o ID completo no hover. |
| Lista com muitos cards | O componente não gerencia paginação. A view pai é responsável. |

## 6. Artefatos Derivados desta Spec

| Artefato | Caminho |
| :--- | :--- |
| Implementação | `src/components/patient-card/PatientCard.tsx` |
| Story (Storybook CSF3) | `src/components/patient-card/PatientCard.stories.tsx` |
