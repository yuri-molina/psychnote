---
type: RouteSpec
title: Spec — Rotas /patients e GET /patients/:id/history
description: Especificação das rotas de gerenciamento e consulta de histórico de pacientes no BFF. Inclui a listagem sintética e a consulta de histórico persistido via Core/ChromaDB.
timestamp: 2026-08-08T18:48:00-03:00
status: active
version: 2.0.0
resource: ./patients.route.ts
related:
  - ../../schemas/index.ts
  - ../plugins/core-client/CoreClient.spec.md
  - ../../../.okf/contracts/bff-api.md
  - ../../../.okf/contracts/core-api.md
---

# Spec — Rotas de Pacientes (`/patients`)

## Identidade das Rotas

| Método | URL | Tag | Descrição |
| :--- | :--- | :--- | :--- |
| GET | /api/patients | Pacientes | Lista os IDs e resumos dos pacientes sintéticos disponíveis na PoC |
| GET | /api/patients/:patient_id/record | Pacientes | Retorna o prontuário histórico sintético solicitado |
| GET | /api/patients/:id/history | Pacientes | Consulta o histórico completo de triagens do paciente persistidas no ChromaDB via Core |

---

## Decisão de Design — Listagem de Pacientes vs. Consulta de Histórico

- **Listagem Estática (`GET /api/patients`):** Para o escopo da PoC acadêmica, a lista de pacientes é estática (`SYNTHETIC_PATIENTS`), servindo apenas para seleção na interface MFE.
- **Histórico Persistido no Core (`GET /api/patients/:id/history`):** O histórico real de avaliações de triagem é mantido e vetorizado no **ChromaDB** gerenciado pelo `psychnote-core`. A nova rota `GET /api/patients/:id/history` consulta diretamente o Core para retornar o histórico cronológico de triagens realizadas para determinado paciente.

---

## Contratos das Rotas

### 1. `GET /api/patients`

#### Resposta de Sucesso — 200 OK
Array de objetos conforme `PatientsResponseSchema`:

```json
[
  { "patient_id": "PAC-010" },
  { "patient_id": "PAC-011" },
  { "patient_id": "PAC-020" }
]
```

---

### 2. `GET /api/patients/:id/history`

#### Parâmetros de Entrada
| Parâmetro | Tipo | Local | Validação | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `string` | Path Param | Mínimo 1 char | Identificador do paciente (`patient_id`) |

#### Resposta de Sucesso — 200 OK
Payload validado pelo schema `PatientRecordSchema` ou array de `TriageHistoryItemSchema`:

```json
{
  "patient_id": "PAC-010",
  "history": [
    {
      "id": "tri-1001",
      "date": "2026-08-08T14:30:00Z",
      "risk_level": "Alto/Iminente",
      "current_note": "Paciente relata ideação suicida ativa com planejamento...",
      "red_flags": ["Ideação ativa", "Plano estruturado"],
      "protection_factors": ["Apoio familiar"],
      "clinical_justification": "Risco elevado devido ao plano e ausência de contenção...",
      "audit_alerts": ["Alerta de risco iminente emitido"]
    }
  ]
}
```

#### Respostas de Erro
| Código | Cenário | Campo `upstream` |
| :--- | :--- | :--- |
| 400 | ID de paciente inválido ou ausente | ausente |
| 404 | Nenhum histórico encontrado para o paciente informado | `'psychnote-core'` |
| 502 | Falha na comunicação com o `psychnote-core` | `'psychnote-core'` |
| 504 | Timeout ao consultar histórico no Core (> 10s) | `'psychnote-core'` |

---

## Fluxo de Execução

### Fluxo para `GET /api/patients/:id/history`

```
1. Registrar rota GET /api/patients/:id/history
2. Extrair `id` de request.params
3. Criar AbortController com timeout de 10000ms
4. Executar coreClient.getPatientHistory(id, signal)
5. SE AbortError:
   - Retornar 504 Gateway Timeout com upstream: 'psychnote-core'
6. SE Core retornar 404:
   - Retornar 404 Not Found com message: 'Histórico não encontrado para o paciente informado.'
7. SE FetchError / UpstreamError:
   - Retornar 502 Bad Gateway com upstream: 'psychnote-core'
8. Validar resposta com schema de histórico (safeParse)
9. Retornar 200 OK com os dados do histórico
```

---

## Logging e LGPD

- **Permitido:** Logar ID do paciente (`id`), quantidade de registros no histórico retornados e tempo de resposta do Core.
- **Proibido (LGPD):** Não gravar o texto de `current_note`, `clinical_justification` ou `final_report` nos logs da aplicação.

---

## Casos de Borda e Cenários de Teste

| Cenário | Entrada | Resposta Esperada |
| :--- | :--- | :--- |
| Paciente com histórico existente | `id: 'PAC-010'` | `200 OK` + JSON do histórico completo |
| Paciente sem histórico registrado no ChromaDB | `id: 'PAC-999'` | `404 Not Found` |
| Falha de conexão com o Core | Qualquer `id` válido | `502 Bad Gateway` (upstream: 'psychnote-core') |
| Timeout na consulta (> 10s) | Qualquer `id` válido | `504 Gateway Timeout` (upstream: 'psychnote-core') |
