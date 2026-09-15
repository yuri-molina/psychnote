# AGENTS.md — psychnote-mfe

Instruções mandatórias para agentes de IA (Claude, Gemini, Cursor, Copilot, etc.) que operam neste repositório. Leia este arquivo completamente antes de executar qualquer tarefa.

---

## 1. Comandos do Projeto

```bash
# Instalar dependências
npm install

# Desenvolvimento standalone (modo cotidiano — porta 5001)
npm run dev

# Build de produção (gera remoteEntry.js para Module Federation)
npm run build

# Modo de integração Module Federation (Remote + Host simultâneos)
npm run dev:mfe

# Verificação de tipos TypeScript
npm run type-check

# Linter
npm run lint

# Storybook (desenvolvimento isolado de componentes — porta 6006)
npm run storybook
```

Nunca invente comandos. Se um script nao existir no package.json, informe ao usuario em vez de executar.

---

## 2. Regras de Comportamento do Agente

1. **Pergunte antes de assumir.** Se uma tarefa for ambígua — especialmente em relacao ao contrato do BFF ou a regras clínicas — pause e solicite esclarecimento. Nunca adivinhe.

2. **Modificacoes cirúrgicas.** Altere apenas o código diretamente relacionado à tarefa. Nao reformate linhas nao tocadas, nao renomeie variaveis existentes, nao reorganize imports sem instrucao explícita.

3. **Verificacao obrigatória pós-tarefa.** Antes de considerar uma tarefa concluída, execute:
   ```bash
   npm run type-check && npm run lint
   ```

4. **Nao instale dependências sem permissao.** Consulte o `package.json` antes de importar bibliotecas. Nunca adicione entradas ao `package.json` sem aprovacao explícita do usuario.

5. **Nao desative testes para fazer o build passar.** Corrija o código subjacente.

6. **Consulte as specs antes de implementar.** Cada componente, hook e view tem um arquivo `.spec.md` co-localizado. Leia-o antes de escrever qualquer linha de implementacao.

7. **Consulte o OKF antes de regras de negócio.** Para lógica clínica, contratos de API ou decisoes arquiteturais, leia primeiro `.okf/index.md` para localizar o artefato relevante.

---

## 3. Stack Tecnológica

| Camada | Tecnologia | Observacao |
| :--- | :--- | :--- |
| Build | Vite 6 | `build.target: 'esnext'` obrigatório |
| Module Federation | @originjs/vite-plugin-federation 1.3.x | Standalone-first. Veja `.okf/architecture/module-federation.md` |
| Framework | React 19 + TypeScript strict | `strict: true` no tsconfig |
| Componentes UI | shadcn/ui | Gerado via CLI, nunca editar `src/components/ui/` manualmente |
| Estilizacao | Tailwind CSS 4 | Prefixo `psy-` obrigatório em TODAS as classes |
| Validacao | Zod 3 | Fonte única de verdade dos tipos de API |
| Async / Cache | TanStack Query 5 | Declarado como singleton no Module Federation |
| Roteamento | React Router 7 | — |

---

## 4. Convencoes de Código

### TypeScript

- `strict: true` ativo. O tipo `any` é proibido. Use `unknown` com type guards se necessário.
- Tipos de API sao inferidos dos schemas Zod: `type TriageResponse = z.infer<typeof TriageResponseSchema>`. Nao declare tipos de API manualmente em paralelo.
- Interfaces de props usam a convencao `interface Props` dentro do arquivo do componente, nao exportadas separadamente, a menos que compartilhadas.

### Componentes React

- Exportacoes nomeadas obrigatórias: `export function ClinicalRiskBadge(...)`.
- Nao use default exports em componentes.
- Componentes acima de 150 linhas devem ser divididos em sub-componentes.
- Nao faca chamadas HTTP ou use hooks de query diretamente em componentes. Esses pertencem a `src/hooks/`.

### Tailwind CSS (REGRA CRÍTICA)

- **TODAS** as classes Tailwind do MFE usam o prefixo `psy-`.
- Correto: `psy-flex psy-items-center psy-bg-primary`
- Errado: `flex items-center bg-primary`
- O prefixo esta configurado em `tailwind.config.js`. Classes sem prefixo nao serao processadas.

### Estilizacao com shadcn/ui

- Use a funcao `cn()` de `src/lib/utils.ts` para classes condicionais.
- Nao sobrescreva estilos via `style={{}}` inline.
- O diretório `src/components/ui/` é gerenciado exclusivamente pelo CLI do shadcn. Nunca edite esses arquivos manualmente.

---

## 5. Mapa de Diretórios

```
psychnote-mfe/
├── .okf/                    Base de conhecimento OKF (arquitetura, contratos, domínio)
├── src/
│   ├── components/          Componentes React reutilizáveis
│   │   ├── ui/              Gerado pelo shadcn/ui — NAO EDITAR
│   │   └── [name]/          Cada componente em seu próprio diretório
│   │       ├── [Name].tsx   Implementacao
│   │       ├── [Name].spec.md  Especificacao SDD — LEIA ANTES DE IMPLEMENTAR
│   │       └── [Name].stories.tsx  Story Storybook
│   ├── views/               Telas da aplicacao
│   │   ├── [ViewName].tsx
│   │   └── [ViewName].spec.md   Spec de layout — LEIA ANTES DE IMPLEMENTAR
│   ├── hooks/               Hooks de dados (TanStack Query)
│   │   ├── useTriage.ts
│   │   └── useTriage.spec.md   Spec de estado (FSM) — LEIA ANTES DE IMPLEMENTAR
│   ├── lib/
│   │   ├── schemas.ts       Schemas Zod — fonte única de verdade dos tipos de API
│   │   ├── api.ts           HTTP client (baseURL via VITE_BFF_URL)
│   │   └── utils.ts         cn() e utilitários
│   ├── App.tsx              Router + layout raiz
│   ├── main.tsx             Entrada standalone (npm run dev)
│   └── PsychnoteMfe.tsx     Entrada Module Federation (exposto via federation)
├── AGENTS.md                Este arquivo
├── CLAUDE.md                Espelho de AGENTS.md para Claude Code
├── GEMINI.md                Espelho de AGENTS.md para Gemini / Antigravity
├── vite.config.ts
├── tailwind.config.js       prefix: 'psy-'
├── components.json          shadcn/ui prefix: 'psy-'
└── .env.local               VITE_BFF_URL=http://localhost:4000 (nao versionado)
```

---

## 6. Base de Conhecimento OKF

A documentacao estruturada do projeto segue o Open Knowledge Format em `.okf/`.

Antes de implementar qualquer funcionalidade, leia `.okf/index.md` para localizar o artefato relevante.

| Necessidade | Artefato OKF |
| :--- | :--- |
| Arquitetura geral e fluxo de dados | `.okf/architecture/overview.md` |
| Configuracao de Module Federation | `.okf/architecture/module-federation.md` |
| Estrutura de diretórios e convencoes | `.okf/architecture/folder-structure.md` |
| Hierarquia de componentes | `.okf/architecture/component-tree.md` |
| Regras de domínio clínico | `.okf/domain/clinical-triage.md` |
| Contrato da Core API | `.okf/contracts/core-api.md` |
| Contrato do BFF | `.okf/contracts/bff-api.md` |
| Por que decisao X foi tomada | `.okf/decisions/` |
| Como rodar o projeto | `.okf/playbooks/project-setup.md` |
| Como fazer build e testar Module Federation | `.okf/playbooks/build-and-federation.md` |

---

## 7. Regras de Domínio Clínico (Invioláveis)

Este projeto opera em domínio de saúde mental com implicacoes clínicas diretas. As regras abaixo nao sao negociáveis.

- **Nenhum dado de paciente deve ser persistido.** localStorage, sessionStorage, cookies, IndexedDB e qualquer forma de persistência no browser sao proibidos para dados clínicos (patient_id, current_note, resultados de triagem). LGPD.

- **Nunca chame o psychnote-core diretamente.** O MFE nao deve fazer HTTP para `localhost:8000`. Todo tráfego de dados vai exclusivamente para o BFF (`localhost:4000` via `VITE_BFF_URL`).

- **Valide todos os responses do BFF com Zod.** Use `TriageResponseSchema.parse(data)` antes de passar qualquer dado clínico para a UI. Uma falha silenciosa em `risk_level` pode resultar em erro clínico grave.

- **O componente ClinicalRiskBadge deve ser renderizado sempre que risk_level estiver presente.** Nunca exiba risco clínico como texto puro sem o componente visual designado.

- **Alertas com prefixo [FALHA CRITICA] exigem tratamento visual de máxima severidade.** Nao trate todos os audit_alerts com o mesmo estilo.

---

## 8. Antipadroes Proibidos

- Chamar `localhost:8000` (Core) diretamente do MFE.
- Usar classes Tailwind sem o prefixo `psy-`.
- Editar arquivos em `src/components/ui/` manualmente.
- Usar o tipo `any` em qualquer contexto.
- Usar `style={{}}` inline para estilizacao.
- Persistir dados clínicos em qualquer mecanismo de armazenamento do browser.
- Renderizar dados do BFF sem passar pelo `schema.parse()` do Zod correspondente.
- Criar componentes com mais de 150 linhas sem extrair sub-componentes.
- Implementar logica de fetch ou mutacao HTTP dentro de componentes React.
- Adicionar dependências ao `package.json` sem aprovacao do usuario.
- Usar `console.log` em código de producao.
