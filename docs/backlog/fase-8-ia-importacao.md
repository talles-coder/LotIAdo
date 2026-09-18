# Fase 8 — IA para Importação Flexível

Entrega desta fase: entrada → processamento por IA → dados estruturados → validação humana → persistência, para CSVs sem padrão fixo e para extração assistida de informações de plantas/imagens. A IA nunca persiste geometria/dados definitivos sem revisão humana (princípio já registrado em [01-analise-requisitos.md](../01-analise-requisitos.md)).

## Épico E8.1 — CSV sem padrão fixo via LLM

### FASE8-EST-01-D1 / FASE8-EST-01-D2 — Estudo: structured output / function calling com LLMs
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** usar um LLM para mapear colunas arbitrárias de um CSV para um schema alvo fixo, de forma confiável (saída estruturada, não texto livre).
- **Conceitos a entender:** structured output / JSON mode / function calling (dependendo do que o modelo local via Ollama suportar); validação da saída do LLM com um schema (ex.: Pydantic) antes de confiar nela; o que fazer quando o LLM erra o formato (retry com o erro de validação no prompt).
- **Material recomendado:** documentação do Ollama sobre modo estruturado/JSON; documentação do Pydantic para validação de saída de LLM (padrão comum: "instructor"-style, mesmo sem usar a lib, usando `model_validate` manualmente).
- **Exercício prático:** dado um CSV de exemplo com colunas em nomes/ordem não previstos, escrever um prompt que retorna o mapeamento coluna→campo em JSON, validar com Pydantic, e tratar o caso de falha de validação com um retry.
- **Critério de conclusão:** exercício mapeia corretamente pelo menos 2 variações diferentes de CSV (nomes de coluna diferentes) para o mesmo schema alvo.
- **Paralelizável:** Sim.

### FASE8-IMPL-01 — Sugestão automática de mapeamento de colunas do CSV
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** a tela de import de CSV (Fase 5) passa a vir com um mapeamento **sugerido** pela IA, que o usuário confirma ou corrige — nunca aplicado automaticamente sem revisão.
- **Descrição:** endpoint que recebe os cabeçalhos do CSV (já existente na Fase 4/5) e retorna, via `LLMProvider`, uma sugestão de mapeamento coluna→campo com um nível de confiança; a tela de mapeamento (Fase 5) pré-preenche os selects com a sugestão, deixando claro que é uma sugestão editável.
- **Pré-requisitos:** FASE8-EST-01-D1.
- **Dependências:** FASE4-IMPL-04, FASE5-IMPL-02.
- **Resultado esperado:** usuário ainda confirma o mapeamento manualmente, mas com menos trabalho.
- **Critérios de aceite:** para 3 CSVs de teste com formatos diferentes, a sugestão acerta a maioria dos campos óbvios (ex.: coluna "Preço (R$)" → campo `preco`); em nenhum caso o sistema importa sem a etapa de confirmação humana.
- **Paralelizável:** Sim, com FASE8-IMPL-02.
- **Conhecimentos novos introduzidos:** uso do LLM para uma tarefa de classificação/mapeamento estruturado, não geração de texto livre.

## Épico E8.2 — Extração assistida de plantas/imagens

### FASE8-EST-02-D1 / FASE8-EST-02-D2 — Estudo: OCR e visão computacional básica para documentos/imagens
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender quando usar OCR/visão computacional clássica versus LLM multimodal para extrair informação de uma imagem de planta, e por que a combinação das duas é mais realista do que confiar só em um LLM multimodal (ver risco em [01-analise-requisitos.md](../01-analise-requisitos.md)).
- **Conceitos a entender:** OCR (ex.: Tesseract, gratuito) para extrair texto/identificação de lotes visíveis na imagem; detecção de contornos com OpenCV para identificar os limites aproximados de um lote na planta; LLM multimodal (se o modelo local disponível suportar) para interpretar texto/rótulos em contexto; por que nenhuma dessas técnicas produz coordenada geográfica real sozinha — isso exige o passo de calibração manual já implementado na Fase 5 (FASE5-IMPL-03).
- **Material recomendado:** documentação do Tesseract OCR; documentação introdutória do OpenCV sobre detecção de contornos (`findContours`); documentação do Ollama sobre modelos multimodais disponíveis localmente (se houver um adequado ao hardware CPU-only da equipe — decisão 3 em [01-analise-requisitos.md](../01-analise-requisitos.md)).
- **Exercício prático:** rodar OCR em uma imagem de planta de exemplo e extrair os textos visíveis (identificações de lote); rodar detecção de contornos na mesma imagem e visualizar os contornos encontrados sobrepostos à imagem original.
- **Critério de conclusão:** consegue explicar, para uma planta de exemplo real, qual técnica resolveria qual parte do problema (texto vs. geometria) e por que nenhuma delas substitui a calibração manual.
- **Paralelizável:** Sim.

### FASE8-IMPL-02 — Extração assistida de identificação/área de lotes a partir de imagem
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** dado um upload de planta, o sistema sugere identificações de lote e um contorno aproximado, que o usuário revisa e corrige no editor de polígono (Fase 5) antes de qualquer persistência.
- **Descrição:** pipeline: OCR sobre a imagem para extrair textos candidatos a identificação de lote; detecção de contornos para sugerir polígonos aproximados (em coordenadas de pixel, não geográficas); resultado apresentado na tela de FASE5-IMPL-03 como uma camada "sugestão da IA" sobreposta à planta, nunca persistida automaticamente — a persistência só ocorre depois do passo de calibração manual e confirmação humana.
- **Pré-requisitos:** FASE8-EST-02-D2.
- **Dependências:** FASE5-IMPL-03, FASE7-IMPL-01 (fila RQ/worker já existente, reaproveitada aqui).
- **Resultado esperado:** o trabalho de desenhar polígono na Fase 5 fica mais rápido (edição de uma sugestão em vez de desenho do zero), sem nunca pular a revisão humana.
- **Critérios de aceite:** para uma planta de teste conhecida, o sistema sugere ao menos algumas identificações de lote corretas via OCR; nenhuma geometria sugerida é gravada no banco sem passar pela tela de revisão/calibração.
- **Paralelizável:** Não pode ser finalizada sem FASE5-IMPL-03 existir (é onde a sugestão é exibida), mas o pipeline de OCR/contornos em si pode ser desenvolvido isoladamente em paralelo.
- **Conhecimentos novos introduzidos:** OCR (Tesseract), detecção de contornos (OpenCV), composição de múltiplas técnicas de IA/visão em um único pipeline de sugestão (não persistência automática).

## Divisão de trabalho e sincronização

- **Dev 1:** FASE8-EST-01/02 → FASE8-IMPL-01 (mapeamento de CSV).
- **Dev 2:** FASE8-EST-01/02 → FASE8-IMPL-02 (extração de imagem).
- **Pontos de sincronização:** nenhum direto entre FASE8-IMPL-01 e FASE8-IMPL-02 (features independentes); ambas dependem apenas das fases 4/5 já concluídas. FASE8-IMPL-02 (processamento de imagem, mais pesado que o de CSV) deve reaproveitar a fila RQ/worker já introduzida na Fase 7 (FASE7-IMPL-01) em vez de processar inline — não é necessário nenhum estudo novo de fila aqui, apenas registrar um novo tipo de job (ex.: `processar_imagem_planta(documento_id)`) no mesmo worker.
