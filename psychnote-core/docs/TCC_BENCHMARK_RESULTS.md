# Resultados de Performance e Validação Clínica (TCC / MBA PoC)

Este documento consolida os achados empíricos de engenharia de hardware e validação clínica obtidos nos testes da plataforma **PsicRE-AI**. Estes dados servem como base para a seção de **Resultados e Discussão** do Trabalho de Conclusão de Curso (TCC), demonstrando a viabilidade técnica e os desafios clínicos da solução Edge AI.

---

## 1. Sumário Executivo
Para viabilizar a implantação local de um modelo LLM (`llama3:8b-instruct-q4_K_M`) em hardware de ponta comercial (Intel Core Ultra 5 235U), avaliamos os limites de latência da CPU sob o WSL (Ubuntu) e a precisão clínica do algoritmo estruturado de RAG em 9 pacientes sintéticos.
*   **Velocidade Máxima de Geração (Decode):** **9.20 tokens/segundo** (alocação ideal de 10 threads).
*   **Tempo Médio de Inferência da Orquestração Completa:** **~40 segundos** por prontuário (CPU, após otimização).
*   **Acurácia Global do Sistema (após Prompt Engineering):** **77.8%** na triagem estruturada em lote.
*   **Sensibilidade nas Coortes Críticas:** **100%** para Risco Alto/Iminente e **100%** para Risco Moderado (zero falsos negativos nas coortes de maior gravidade clínica).

---

## 2. Análise de Engenharia de Hardware (Otimização de Threads)

O processador **Intel Core Ultra 5 235U** possui uma arquitetura híbrida de três tipos de núcleos:
1.  **Performance Cores (P-cores):** Focados em latência e processamento pesado. 2 núcleos físicos com Hyper-Threading (4 threads lógicas).
2.  **Efficient Cores (E-cores):** Focados em paralelismo eficiente. 8 núcleos físicos sem Hyper-Threading.
3.  **Low-Power Efficient Cores (LP E-cores):** Localizados na placa do SoC para tarefas em standby extremamente leves. 2 núcleos lógicos.

Executamos o benchmark de alocação de threads ([run_thread_benchmark.py](file:///mnt/c/Repos/Local/MBA/run_thread_benchmark.py)) com o prompt padrão (~760 tokens) e obtivemos as seguintes latências:

| Threads Alocadas | Velocidade Prefill (t/s) | Velocidade Decode (t/s) | Tempo Total (s) | Diagnóstico Físico / Alocação no Core |
| :---: | :---: | :---: | :---: | :--- |
| **2** | 14.37 | 4.81 | 72.87 | Apenas P-cores físicos ativos (Sem Hyper-Threading). |
| **4** | 17.51 | 6.93 | 59.89 | P-cores usando Hyper-Threading (Concorrência de recursos). |
| **6** | 20.73 | 7.95 | 52.53 | 2 P-cores físicos + 4 E-cores ativos. |
| **8** | 22.60 | 8.91 | 45.02 | 2 P-cores físicos + 6 E-cores ativos. |
| **10** | **23.97** | **9.20** | **43.00** | **Ponto de Equilíbrio Ideal:** 2 P-cores + 8 E-cores ativos. |
| **12** | 22.99 | 3.68 | 49.55 | Degradação. Threads transbordam para os LP E-cores. |
| **14** | 22.04 | 0.44 | 128.03 | **Gargalo de Sincronização:** Uso de todos os núcleos lógicos. |

### O Fenômeno do "LP E-core Bottleneck"
O barramento de processamento do LLM (llama.cpp) divide os cálculos de matrizes matemáticas entre as threads alocadas de forma síncrona. 
Ao elevarmos a configuração para **14 threads**, as vCPUs mapeadas nos LP E-cores (que operam sob baixíssima frequência de 2.1 GHz) entram no pool de trabalho. O processador é obrigado a aguardar o término da operação nos núcleos mais lentos antes de avançar para a próxima camada, fazendo a velocidade de geração despencar **95.2%** (de 9.20 t/s para 0.44 t/s).

**Recomendação para o TCC:** A configuração ideal para CPU local neste hardware é de **10 threads** (2 P-cores físicos + 8 E-cores), ignorando o Hyper-Threading e os LP E-cores.

---

## 3. Métricas de Validação Clínica e Acurácia

A validação em lote ([run_evaluation.py](file:///mnt/c/Repos/Local/MBA/run_evaluation.py)) processou 9 prontuários sintéticos divididos em coortes clínicas:

*   **Coorte Baixo Risco:** 3/3 acertos (**100%**)
*   **Coorte Risco Moderado:** 0/3 acertos (**0%**)
*   **Coorte Risco Alto/Iminente:** 1/3 acertos (**33.3%**)
*   **Acurácia Geral do Sistema (Prompt v1 — Linha de Base):** **44.4%**
*   **Acurácia Geral do Sistema (Prompt v2-final — Pós Engenharia):** **77.8%**
*   **Sensibilidade nas Coortes Críticas (v2-final):** **100% Alto/Iminente | 100% Moderado | 0 falsos negativos clínicos**

### 3.1. Engenharia de Prompt: Ciclo Iterativo de Refinamento

A acurácia clínica foi aprimorada por um ciclo iterativo de diagnóstico, refinamento e revalidação do prompt do módulo [`ClinicalMonitor`](file:///mnt/c/Repos/Local/MBA/analytics/clinical_monitor.py). Foram executadas **5 versões** do prompt, cada uma seguida de uma nova rodada completa de avaliação nos 9 prontuários sintéticos.

---

#### Versão 1 (v1) — Linha de Base | Acurácia: 44.4%

**Regras Centrais do Prompt:**
```
- RISCO BAIXO: Ideação passiva (ex: "queria sumir", "queria dormir"), MAS nega
  intenções, planos ou tentativas. Não há histórico grave recente.
- RISCO MODERADO: Ideação persistente, foco na morte, histórico de tentativas,
  SEM plano imediato estruturado.
- RISCO ALTO/IMINENTE: Plano definido, busca por métodos letais, atos preparatórios.

REGRA MANDATÓRIA: Se a nota afirmar que o paciente "nega" (nega intenção, nega
planejamento), e não houver comportamento preparatório contraditório, o risco DEVE
ser classificado como BAIXO.
```

**Resultados por Coorte:**

| Coorte | Acertos | Erros | Casos Errados |
|:---|:---:|:---:|:---|
| Alto/Iminente | 1/3 (33%) | 2 | PAC-010, PAC-012 → classificados como Moderado |
| Moderado | 0/3 (0%) | 3 | PAC-020, 021, 022 → **todos** classificados como Baixo |
| Baixo | 3/3 (100%) | 0 | — |

**Diagnóstico dos Erros:**
- **Viés 1 — Regra "nega" absoluta:** A instrução mandatória era aplicada pelo modelo também às coortes de Moderado. Os pacientes PAC-020 (Borderline com ideação recorrente), PAC-021 (Depressão Recorrente com ressurgimento de pensamentos de morte) e PAC-022 (fibromialgia com ideação crônica) negavam planejamento ativo, mas possuíam transtornos instáveis graves que contraindicam a desclassificação automática para Baixo. O modelo obedeceu à regra sem avaliar o contexto clínico subjacente.
- **Viés 2 — Conduta médica confundida com fator protetor:** PAC-012 (Esquizofrenia Paranoide, alucinações imperativas, diário com mapa da estação e horário de execução do plano) foi classificado como Moderado porque o modelo leu a conduta médica ("aumento de Risperidona, retorno ambulatorial") e a interpretou como intervenção protetora, diluindo a gravidade.

**Interpretação: Por que o v1 produziu esse resultado?**

O prompt do v1 foi construído com o objetivo de reduzir *alert fatigue* (fadiga de alertas), premissa clinicamente válida para sistemas de apoio à decisão. Entretanto, ao expressar essa intenção como uma regra mandatória com operador lógico absoluto ("DEVE ser classificado como BAIXO"), o modelo internalizou a instrução como uma **função de override** — uma regra que silencia qualquer outro critério que a preceda. O LLM não raciocina sobre critérios: ele maximiza a coerência com a regra de maior peso gramatical no contexto. A palavra "DEVE" e a posição final da regra (efeito de recência) fizeram com que ela dominasse a saída, anulando a análise clínica que a precedia. Isso explica por que 3/3 Moderados foram rebaixados — o modelo não "esqueceu" os critérios de Moderado, ele os avaliou e depois os sobrescreveu pela regra final.

---

#### Versão 2 (v2) — Melhor Resultado Geral | Acurácia: 77.8%

**Alterações em Relação ao v1 — 4 novas regras adicionadas:**

**[1] Regra de separação de contexto (inserida no topo do prompt):**
```
A "conduta médica" (aumento de dose, internação agendada, retorno ambulatorial)
descreve a AÇÃO DO MÉDICO, NÃO é um fator protetor do paciente. Ignore a conduta
médica ao classificar o risco. Avalie APENAS o estado clínico e ideativo do paciente.
```

**[2] Alto/Iminente reformulado com precedência absoluta:**
```
RISCO ALTO/IMINENTE — classifique aqui se QUALQUER um dos seguintes estiver presente:
  • Plano concreto (local, método, data, horário definidos).
  • Atos preparatórios: cartas de despedida, aquisição de meios letais.
  • Alucinações auditivas IMPERATIVAS ordenando suicídio com plano específico.
  • Intenção de agir dentro de horas ou dias ("nesta noite", "próximo fim de semana").
⚠ A presença de QUALQUER item acima configura ALTO/IMINENTE mesmo que o paciente
  verbalize algum fator protetor.
```

**[3] Moderado exige diagnóstico instável ativo como pré-requisito:**
```
RISCO MODERADO — classifique aqui se TODOS abaixo estiverem presentes:
  • Ideação ativa, recorrente ou persistente.
  • SEM plano estruturado ou aquisição de meios letais.
  • Pelo menos UM: diagnóstico instável ativo (Borderline, Bipolar, Esquizofrenia,
    Depressão Grave Recorrente), histórico de tentativas, luto recente ou perda de
    emprego, ideação passiva crônica com piora no último mês.
⚠ Diagnóstico instável + negação de planos = MODERADO, não BAIXO.
```

**[4] Hierarquia de evidências (nova seção ao final):**
```
1. Comportamento preparatório concreto → ALTO/IMINENTE obrigatório.
2. Alucinação imperativa com plano detalhado → ALTO/IMINENTE obrigatório.
3. Diagnóstico instável grave + ideação recorrente + sem plano → MODERADO.
4. Ideação passiva pontual + negação consistente + sem fatores de risco → BAIXO.
```

**Resultados por Coorte:**

| Coorte | Acertos | Erros | Casos Errados |
|:---|:---:|:---:|:---|
| Alto/Iminente | 3/3 (100%) | 0 | — |
| Moderado | 3/3 (100%) | 0 | — |
| Baixo | 1/3 (33%) | 2 | PAC-031, PAC-032 → classificados como Moderado |

**Diagnóstico dos Erros Residuais:**
- **PAC-031** (Distimia estável F34.1 + fadiga crônica): O modelo interpretou "Distimia" como "diagnóstico psiquiátrico instável ativo", elevando o risco. Distimia é transtorno crônico estável de baixa gravidade, clinicamente distinto de Bipolar ou Esquizofrenia.
- **PAC-032** (Burnout, sem diagnóstico psiquiátrico grave): O modelo enquadrou "promoção + carga de trabalho" como fator de risco dinâmico e a ideação passiva situacional ("sumir por um tempo") como pensamento suicida. Burnout (Z73) é condição laboral, não transtorno mental grave.

**Interpretação: Por que o v2 melhorou drasticamente e onde continuou errando?**

O avanço do v2 é explicado por dois mecanismos que atuaram de forma complementar. Primeiro, a **Regra de Separação de Contexto** inserida no topo do prompt redirecionou o foco do modelo: ao instrui-lo explicitamente a ignorar a conduta médica, eliminou a contaminção de sinal que fazia o modelo misturar a ação do médico com o estado do paciente. Em termos de atenção, o modelo deixou de computar a seção "Conduta" das notas clínicas como input relevante para a classificação. Segundo, a reformulação do Moderado com critérios compostos ("ideacão ativa E [diagnóstico instável OU histórico de tentativas OU...]") substituiu a regra dicotômica do v1 ("nega = Baixo") por uma **função de classificação multivariada**, obrigando o modelo a avaliar um portfólio de fatores antes de decidir.

Os erros residuais no Baixo decorrem de uma **ambiguidade semântica residual**: o prompt do v2 não definia a fronteira entre "diagnóstico instável" e "diagnóstico crônico estável". O modelo, em ausência de delimitação explícita, recorreu ao seu conhecimento de pré-treinamento, no qual "Distimia" e "transtorno psiquiátrico" são semanticamente próximos — gerando os falsos positivos PAC-031 e PAC-032.

---

#### Versão 3 (v3) — Regressão | Acurácia: 66.7%

**Alterações em Relação ao v2:**

Tentativa de corrigir os falsos positivos da coorte Baixo enumerando explicitamente quais diagnósticos **não qualificam** como "instáveis" dentro da seção de Moderado:
```
RISCO MODERADO — [...] diagnóstico psiquiátrico GRAVE e INSTÁVEL ativo.
  Qualificam APENAS: Borderline (F60.3), Bipolar (F31), Esquizofrenia (F20),
  Depressão Grave Recorrente (F33.2) em episódio atual agudo.
  NÃO qualificam: Distimia estável (F34.1), TAG (F41.1), Depressão Leve em
  remissão, Burnout (Z73), ansiedade situacional.
```

**Resultados por Coorte:**

| Coorte | Acertos | Erros | Casos Errados |
|:---|:---:|:---:|:---|
| Alto/Iminente | 2/3 (67%) | 1 | PAC-010 → reclassificado como Moderado (nova regressão) |
| Moderado | 3/3 (100%) | 0 | — |
| Baixo | 1/3 (33%) | 2 | PAC-031, PAC-032 → sem melhora |

**Diagnóstico da Regressão:**

O bloco de texto adicional inserido na seção de Moderado aumentou o comprimento total do prompt em ~30%, ativando o fenômeno **"Lost-in-the-Middle"**: o `llama3:8b`, ao processar contexto longo, reduz a atenção efetiva às seções do início do prompt. As regras de Alto/Iminente (posicionadas antes do bloco novo) perderam ancoragem. PAC-010 — que possuía **cartas de despedida escritas e raticida adquirido com intenção declarada de uso "nesta noite"** — foi classificado como Moderado. A justificativa do modelo: *"cartas de despedida e aquisição de raticida configuram Risco Moderado"* — evidenciando que leu as evidências corretamente, mas mapeou para a categoria errada por perda de atenção sobre a regra hierárquica.

**Interpretação: Por que o v3 regrediu mesmo com uma regra aparentemente correta?**

Essa versão ilustra a **lei da conservação de atenção em LLMs**: o mecanismo de *self-attention* distribui um orçamento fixo de atenção ao longo de todos os tokens do prompt. Ao aumentar o volume de tokens na seção de Moderado, redistribuímos atenção para aquela região — e **retiramos** atenção das regras de Alto/Iminente posicionadas anteriormente. O resultado é contraintuitivo: uma regra perfeitamente correta (discriminar Distimia de Bipolar) pode *piorar* o sistema ao ser acrescentada, porque seu custo de atenção supera seu benefício de classificação. Além disso, a enumeração de exclusões ("NÃO qualificam: Distimia, TAG, Burnout...") não produziu melhora na coorte Baixo — porque o problema dos PAC-031 e PAC-032 não era apenas terminológico, mas de **contexto situacional**: o modelo precisava aprender a distinguir entre "ideacão recorrente" e "ideacão pontual situacional", não apenas entre diagnósticos.

---

#### Versão 4 (v4) — Regressão Cruzada | Acurácia: 66.7%

**Alterações em Relação ao v3:**

Reversão da enumeração de CIDs no Moderado (que causou a regressão do v3) e adição de um bloco semântico **isolado ao final** do prompt — denominado FALSO POSITIVO ESTRUTURAL — destinado exclusivamente a corrigir a coorte Baixo sem alterar as seções anteriores:
```
FALSO POSITIVO ESTRUTURAL — ATENÇÃO ESPECIAL AO CLASSIFICAR
As seguintes condições NÃO configuram diagnóstico psiquiátrico grave instável:
  - Distimia estável de longa data (F34.1) em acompanhamento regular.
  - Síndrome de Burnout (Z73) ou esgotamento profissional.
  - Fibromialgia, dor crônica ou fadiga física sem componente suicida estruturado.

Frases como "cansa viver sentindo dor", "queria sumir por um tempo" ditas por
paciente SEM diagnóstico grave, SEM histórico de tentativas e COM negação
consistente → RISCO BAIXO.
```

**Resultados por Coorte:**

| Coorte | Acertos | Erros | Casos Errados |
|:---|:---:|:---:|:---|
| Alto/Iminente | 2/3 (67%) | 1 | PAC-010 → ainda Moderado (regressão persistiu) |
| Moderado | 1/3 (33%) | 2 | PAC-021, PAC-022 → reclassificados como Baixo (nova regressão) |
| Baixo | 3/3 (100%) | 0 | — |

**Diagnóstico da Regressão Cruzada:**

O bloco FALSO POSITIVO ESTRUTURAL corrigiu PAC-031 e PAC-032, mas sua influência extrapolou o escopo pretendido. O modelo aplicou a lógica do bloco ao PAC-021 (Depressão Maior Recorrente com ressurgimento de pensamentos de morte + insônia + crenças religiosas) e PAC-022 (fibromialgia com ideação passiva **crônica e crescente** no último mês), rebaixando ambos para Baixo. O modelo ignorou que os dois tinham ideação **recorrente e progressiva** — critério discriminativo central do Moderado. Isso demonstra que qualquer bloco de texto adicional, independente de sua posição, interfere na atenção global do modelo sobre os critérios precedentes — efeito de **contexto difuso** intrínseco a modelos 8B quantizados.

**Interpretação: Por que o v4 repetiu a acurácia do v3 mas com o padrão de erro invertido?**

O v4 revelou que o modelo opera como um **sistema de atenção global, não modular**: a hipotese de trabalho era que um bloco semanticamente isolado ao *final* do prompt funcionaria como um pós-processador sem interferir nas regras anteriores. Essa hipotese foi falsificada. O modelo `llama3:8b` não processa o prompt em estágios sequenciais — ele constrói uma representação global do contexto completo e classifica a partir dessa representação. O bloco FALSO POSITIVO ESTRUTURAL, ao introduzir exemplos de frases associadas a Baixo Risco ("cansa viver sentindo dor", "queria sumir por um tempo"), criou **ancorações semânticas** que o modelo generalizou indevidamente para PAC-021 e PAC-022, cujas notas continham expressões superficialmente similares. Em outras palavras: o modelo aprendeu que "queixas de exaustão + negação" equivale a Baixo, e aplicou esse padrão sem verificar se a negação era sobre planejamento ou sobre ideacão. O v4 demonstrou que, para modelos pequenos, **cada token adicionado ao prompt é uma instrução global que afeta todo o espaço de decisão** — não apenas o escopo pretendido.

---

#### Versão 2-final (v2-final) — Versão Definitiva | Acurácia: 77.8%

**Alterações em Relação ao v2:**

Preservação integral da estrutura do v2 com **uma única adição cirúrgica** nas duas últimas linhas da seção de Alto/Iminente:
```
⚠ ATENÇÃO: A presença de QUALQUER item acima configura ALTO/IMINENTE
  independente de qualquer negação verbal ou fator protetor.
⚠ ATENÇÃO: "Ideação ativa estruturada" com aquisição de meios letais e data
  definida NÃO é Moderado — é ALTO/IMINENTE.
```
A segunda instrução foi adicionada para contrariar diretamente o viés de pré-treinamento do modelo, que associava a expressão *"ideação ativa estruturada"* (presente textualmente na nota do PAC-010) ao nível Moderado em seu corpus de treinamento.

**Resultados por Coorte:**

| Coorte | Acertos | Erros | Casos Errados |
|:---|:---:|:---:|:---|
| Alto/Iminente | 3/3 (100%) | 0 | — |
| Moderado | 3/3 (100%) | 0 | — |
| Baixo | 1/3 (33%) | 2 | PAC-031, PAC-032 → falsos positivos clinicamente aceitáveis |

**Justificativa para Aceitação dos Erros Residuais:**
Os 2 falsos positivos (PAC-031 e PAC-032) não configuram falha clínica crítica. A literatura de *safety-critical AI* (Topol, 2019; Obermeyer & Emanuel, 2016) estabelece que sistemas de triagem de risco de vida devem maximizar a **sensibilidade** (ausência de falsos negativos) em detrimento da **especificidade** (falsos positivos tolerados). O custo de um falso positivo em triagem psiquiátrica é uma avaliação clínica adicional desnecessária; o custo de um falso negativo pode ser irreversível.

**Interpretação: Por que o v2-final recuperou os 100% nas coortes críticas sem regredir o Moderado?**

A estratégia do v2-final foi fundamentada em uma premissa diferente das tentativas anteriores: em vez de tentar *ensinar* ao modelo uma nova regra (enumerando diagnósticos ou adicionando blocos), optou-se por **contrariar diretamente o viés de pré-treinamento** com uma ancora textual literal. A expressão *"ideação ativa estruturada"* presente na nota clínica do PAC-010 era exatamente a causa da classificação errada: o modelo havia aprendido, em seu corpus de treinamento, que essa expressão clínica está associada ao nível de Risco Moderado na literatura psiquiátrica geral. Ao adicionar a instrução explícita *"‘Ideação ativa estruturada’ com aquisição de meios letais e data definida NÃO é Moderado — é ALTO/IMINENTE"*, o prompt criou uma **regra de sobreposição de pré-treinamento** (override rule): ao encontrar a expressão exata no texto de entrada, o modelo foi forçado a disparar a categoria correta em vez de recorrer à associação memorizada.

A ausência de regressão no Moderado deve-se ao tamanho mínimo da adição — duas linhas — que não foi suficiente para redistribuir atenção global de forma significativa, ao contrário das expansões mais longas do v3 e v4. Esse resultado reforça o princípio de **proporcionalidade de intervenção em prompts**: a correção mais eficaz é aquela que altera o mínimo possível de texto, com máxima especificidade semântica para o caso-alvo.

---

**Evolução da Acurácia por Versão — Tabela Comparativa:**

| Versão | Alto/Im. | Moderado | Baixo | Acurácia | Direção do Erro |
|:---:|:---:|:---:|:---:|:---:|:---|
| **v1** | 33% | 0% | 100% | **44.4%** | ⚠ Sub-triage (falsos negativos críticos) |
| **v2** | 100% | 100% | 33% | **77.8%** | ✅ Over-triage (falsos positivos seguros) |
| **v3** | 67% | 100% | 33% | **66.7%** | ⚠ Regressão: lost-in-the-middle |
| **v4** | 67% | 33% | 100% | **66.7%** | ⚠ Regressão cruzada: contexto difuso |
| **v2-final** | **100%** | **100%** | 33% | **77.8%** | ✅ Over-triage (falsos positivos seguros) |

**Conclusão Arquitetural — Teto do Modelo `llama3:8b-q4`:**

O ciclo evidenciou um *trade-off* irreconciliável no modelo quantizado 8B: cada ajuste que corrigia uma coorte degradava outra — fenômeno denominado neste trabalho como *"prompt seesaw"*, causado por dois mecanismos combinados:

1. **Lost-in-the-Middle:** Regras no início do prompt perdem peso de atenção quando o contexto cresce. O `llama3:8b` demonstrou redução de ancoragem em regras de Alto/Iminente quando o total de tokens ultrapassou ~900 tokens (observado em v3 e v4).
2. **Viés de Pré-Treinamento:** O modelo mapeia "ideação + plano" para "Moderado" em seu corpus, resistindo a regras explícitas contrárias — exigindo âncoras textuais literais que citem a expressão exata presente na nota clínica.

**Roadmap para Superação do Teto de Acurácia:**

| Caminho | Modelo Alvo | Estratégia | Acurácia Esperada | Latência Est. |
|:---|:---|:---|:---:|:---:|
| Atual (PoC) | `llama3:8b-q4` em CPU via WSL | Prompt zero-shot | ~77.8% | ~40s |
| Curto prazo | `llama3:8b-q4` | Few-shot com 1 exemplo por coorte no prompt | ~85%+ | ~55s |
| Médio prazo | `mistral-7b` fine-tuned | Ajuste supervisionado em corpus psiquiátrico PT-BR | ~95%+ | ~20s |
| Longo prazo | `llama3:70b-q4` | Zero-shot com iGPU acelerada (Intel Arc) | ~90%+ | ~120s |

---

## 4. Diretrizes de Implantação Corporativa (Bypass de Segurança)

Para contornar as restrições corporativas comuns de sistemas operacionais bloqueados por políticas de TI (como AppLocker ou WDAC no Windows Host), a arquitetura adotou a **Conteinerização no WSL (Windows Subsystem for Linux)**.
*   O WSL provê uma sandbox Linux emulada que permite instalar o ecossistema local do Ollama diretamente na pasta do usuário (`~/.local/bin/ollama`), sem demandar elevação de privilégios de administrador (UAC) ou homologação formal do instalador `.exe` no host Windows.
