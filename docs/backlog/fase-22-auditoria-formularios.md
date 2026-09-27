# Fase 22 — Auditoria e Robustez de Formulários de Cadastro

Entrega desta fase: os formulários de cliente e corretor deixam de ter só validação "não-vazio" e passam a validar CPF/CNPJ por dígito verificador, contato por formato real (e-mail ou telefone), e ganham os campos que faltavam para um cadastro imobiliário brasileiro de verdade — sempre com validação espelhada no backend (defesa em profundidade, mesmo princípio já usado para RLS/tenant).

## Levantamento de código (2026-09-27)

Confirmado por leitura direta do repositório antes de escrever esta fase:

- **Cliente** (`mobile/app/clientes/novo.tsx`, sem tela de edição): campos `nome`, `documento` (rotulado "CPF ou CNPJ", `keyboardType="numeric"`, sem máscara), `contato` (aceita telefone OU e-mail livremente). Validação = só `.trim() !== ''` nos três campos. Backend (`backend/app/clientes/interface/schemas.py`, `ClienteCreateRequest`/`ClienteUpdateRequest`) espelha exatamente isso: três `str` sem nenhum `validator`/`constr`. **CPF é coletado mas nunca validado por dígito verificador, em nenhuma das duas pontas.**
- **Corretor** (`mobile/app/corretores/novo.tsx` + `[id].tsx` para edição): campos `nome`, `contato` (mesma validação frouxa); `usuario_id` existe no schema mas não aparece no formulário. Backend (`backend/app/corretores/interface/schemas.py`) igualmente sem validators. **Não coleta CPF nem CRECI.**
- **Lote/Loteamento**: não têm formulário manual de cadastro (população via import de CSV/shapefile, Fase 4/8) — fora do escopo desta fase.
- Nenhuma lib de validação (Zod/Yup) existe no mobile hoje — decisão D17 em `03-decisoes-tecnicas.md`, já fechada em 2026-09-27: **Zod + react-hook-form**.

## Épico E22.1 — Fundamentos

### FASE22-EST-01-D1 / FASE22-EST-01-D2 — Estudo: validação de formulário com Zod + react-hook-form no Expo
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender como aplicar Zod (D17, já decidida) e integrar com os componentes de formulário já existentes (`Field`, React Native Paper).
- **Conceitos a entender:** schema de validação (Zod: `.refine()` para regra customizada como dígito verificador de CPF); `react-hook-form` + `zodResolver` para ligar schema a inputs controlados; mensagens de erro por campo; validação em `onBlur` vs. `onSubmit`.
- **Material recomendado:** documentação oficial do Zod; documentação do `react-hook-form` (integração com Zod).
- **Exercício prático:** validar um formulário de teste com 3-4 campos (incluindo um campo com regra customizada, ex. CEP) usando Zod + react-hook-form.
- **Critério de conclusão:** formulário de teste rejeita entrada inválida com mensagem de erro por campo.
- **Paralelizável:** Sim.

## Épico E22.2 — Validação de documento e contato

### FASE22-IMPL-01 — Validação de CPF/CNPJ por dígito verificador (mobile + backend)
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** um CPF ou CNPJ com dígito verificador inválido é rejeitado tanto na tela quanto na API, não só formato/comprimento.
- **Descrição:** função pura de validação (algoritmo padrão de dígito verificador do CPF de 11 dígitos e do CNPJ de 14 dígitos) implementada uma vez e reaproveitada: no backend como `validator` do Pydantic em `ClienteCreateRequest`/`ClienteUpdateRequest.documento`; no mobile como regra do schema de D17. Campo `documento` passa a aceitar máscara (`000.000.000-00` ou `00.000.000/0000-00`) detectando automaticamente CPF vs. CNPJ pelo comprimento.
- **Pré-requisitos:** FASE22-EST-01-D1.
- **Dependências:** `backend/app/clientes/interface/schemas.py`, `mobile/app/clientes/novo.tsx`.
- **Resultado esperado:** CPF/CNPJ com dígito verificador incorreto é rejeitado com mensagem clara nas duas pontas; CPF/CNPJ válido (incluindo os de teste conhecidos, ex. `111.444.777-35`) passa.
- **Critérios de aceite:** teste unitário do algoritmo cobre casos válidos e inválidos conhecidos (incluindo os "CPFs" clássicos de teste como `000.000.000-00`, que devem ser rejeitados apesar de passarem por regex simples).
- **Paralelizável:** Sim, com FASE22-IMPL-02.
- **Conhecimentos novos introduzidos:** algoritmo de dígito verificador de CPF/CNPJ.

### FASE22-IMPL-02 — Validação de contato (e-mail ou telefone) por formato real
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** o campo de contato deixa de aceitar qualquer string não-vazia — precisa parecer um e-mail válido ou um telefone brasileiro válido.
- **Descrição:** regra de validação que tenta e-mail (regex padrão) e, se não for e-mail, exige formato de telefone BR (DDD + número, com ou sem `+55`); aplicada em `Cliente` e `Corretor`, mobile e backend.
- **Pré-requisitos:** FASE22-EST-01-D2.
- **Dependências:** mesmos arquivos de FASE22-IMPL-01, mais os schemas/telas de corretor.
- **Resultado esperado:** contato inválido (ex.: "abc", "12345") é rejeitado; e-mail e telefone válidos são aceitos.
- **Critérios de aceite:** teste cobre pelo menos 3 formatos válidos de telefone (com/sem DDI, com/sem espaço) e 2 formatos válidos de e-mail, além de casos inválidos.
- **Paralelizável:** Sim, com FASE22-IMPL-01.
- **Conhecimentos novos introduzidos:** nenhum além de FASE22-EST-01.

## Épico E22.3 — Campos completos do Cliente

### FASE22-IMPL-03 — Campos adicionais do cadastro de Cliente
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** o cadastro de cliente coleta o mínimo esperado de um cliente de imobiliária brasileira, não só nome/documento/contato.
- **Descrição:** novos campos (todos com migration no backend): RG (opcional, string livre com limite de tamanho), data de nascimento (date picker no mobile, validada como data passada e maior de 18 anos — regra de negócio simples, não bloqueante), endereço completo (CEP com formato `00000-000`, rua, número, complemento opcional, bairro, cidade, UF de lista fechada), estado civil (enum: solteiro/casado/divorciado/viúvo/união estável), telefone secundário (opcional, mesma validação de FASE22-IMPL-02), observações (texto livre opcional). Todos os campos novos são opcionais exceto os já existentes, para não quebrar clientes já cadastrados.
- **Pré-requisitos:** nenhum estudo novo além de FASE22-EST-01.
- **Dependências:** FASE22-IMPL-01/02 (reaproveita a validação de documento/contato).
- **Resultado esperado:** formulário de cliente com os campos novos, todos validados; clientes existentes continuam válidos (campos novos nulos).
- **Critérios de aceite:** migration aplica sem erro sobre dados de teste existentes; CEP/UF inválidos são rejeitados; data de nascimento futura é rejeitada.
- **Paralelizável:** Sim, com FASE22-IMPL-04.
- **Conhecimentos novos introduzidos:** nenhum.

## Épico E22.4 — Campos completos do Corretor

### FASE22-IMPL-04 — Campos adicionais do cadastro de Corretor (incluindo CRECI)
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** o cadastro de corretor passa a exigir CRECI (obrigatório por ser a licença profissional) e ganha os demais campos relevantes.
- **Descrição:** novos campos: CPF (obrigatório, reaproveita validação de dígito verificador de FASE22-IMPL-01), CRECI (obrigatório, formato livre por estado — ex. `12345-F`/`SP`, validado só por presença/comprimento mínimo, sem algoritmo de dígito verificador porque não existe um público), data de nascimento (mesma regra de FASE22-IMPL-03), endereço completo (mesma estrutura de FASE22-IMPL-03), comissão padrão (percentual, 0-100, opcional — valor default aplicado em negociações futuras, não retroativo), telefone secundário (opcional).
- **Pré-requisitos:** nenhum estudo novo além de FASE22-EST-01.
- **Dependências:** FASE22-IMPL-01/02.
- **Resultado esperado:** corretor não pode ser cadastrado sem CPF válido e CRECI preenchido; demais campos novos opcionais.
- **Critérios de aceite:** tentativa de criar corretor sem CRECI é rejeitada com mensagem clara; corretores existentes sem CRECI continuam funcionando até serem editados (migração não força preenchimento retroativo obrigatório, só na criação/edição nova).
- **Paralelizável:** Sim, com FASE22-IMPL-03.
- **Conhecimentos novos introduzidos:** nenhum.

## Épico E22.5 — Autopreenchimento, seleção fechada e mídia

### FASE22-IMPL-05 — Autocomplete de CEP (ViaCEP) e campos de seleção fechada (estado, cidade, país)
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** o usuário digita só o CEP e rua/número/bairro/cidade/UF vêm preenchidos sozinhos; estado, cidade e país deixam de ser texto livre (fonte de erro de digitação/inconsistência) e viram seleção fechada.
- **Descrição:** ao digitar um CEP válido (8 dígitos), chamada à API pública gratuita ViaCEP (`viacep.com.br`, sem autenticação, sem custo) preenche rua/bairro/cidade/UF automaticamente, deixando número e complemento para o usuário digitar; campo de UF vira select fechado (27 opções); campo de cidade vira autocomplete alimentado pela API de localidades do IBGE (gratuita, sem autenticação) filtrado pela UF já selecionada — não é uma lista fechada hardcoded de ~5.570 municípios, é busca dinâmica; campo de país vira select fechado com "Brasil" como única opção por ora (modelado como lista extensível, não hardcoded no componente, para não exigir retrabalho se o produto um dia expandir). Falha da API (CEP não encontrado ou serviço fora do ar) não bloqueia o formulário — usuário pode preencher manualmente, o autocomplete é um atalho, não uma exigência.
- **Pré-requisitos:** nenhum estudo novo (é integração de API REST simples, já dominada desde a Fase 0).
- **Dependências:** FASE22-IMPL-03 (campo de endereço do cliente), FASE22-IMPL-04 (campo de endereço do corretor).
- **Resultado esperado:** digitar um CEP válido de teste preenche os campos de endereço corretamente; CEP inválido/inexistente não trava o formulário.
- **Critérios de aceite:** teste com CEP conhecido confere os campos preenchidos; teste com a API indisponível (mockada como erro) confirma que o formulário continua editável manualmente.
- **Paralelizável:** Sim, com FASE22-IMPL-06.
- **Conhecimentos novos introduzidos:** integração com ViaCEP e API de localidades do IBGE.

### FASE22-IMPL-06 — Foto de perfil do usuário (avatar)
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** cada usuário (corretor, gestor, cliente) pode ter uma foto de perfil própria, além do logo da imobiliária (que é do tenant, não do usuário — ver `FASE14-IMPL-05`).
- **Descrição:** campo de avatar no perfil do usuário (não no cadastro de cliente/corretor como entidade de negócio, e sim no `User` — Fase 0), upload reaproveitando o storage já abstraído (MinIO/S3, Fase 5); exibido nas telas onde o usuário aparece (ex. responsável pelo lead na Fase 11, autor de mensagem no histórico da Fase 12); fallback para iniciais do nome quando não há foto (nunca ícone genérico quebrado).
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE5 (storage).
- **Resultado esperado:** usuário de teste consegue subir/trocar/remover a própria foto, visível nas telas relevantes.
- **Critérios de aceite:** upload de arquivo que não é imagem é rejeitado com mensagem clara; usuário sem foto mostra iniciais, nunca quebra o layout.
- **Paralelizável:** Sim, com FASE22-IMPL-05.
- **Conhecimentos novos introduzidos:** nenhum além do já coberto em storage (Fase 5).

## Divisão de trabalho e sincronização

- **Dev 1:** FASE22-EST-01 → FASE22-IMPL-01 (documento) → FASE22-IMPL-03 (campos de cliente) → FASE22-IMPL-05 (CEP/selects).
- **Dev 2:** FASE22-EST-01 → FASE22-IMPL-02 (contato) → FASE22-IMPL-04 (campos de corretor) → FASE22-IMPL-06 (avatar).
- **Pontos de sincronização:** a função de validação de documento (FASE22-IMPL-01) e de contato (FASE22-IMPL-02) precisam estar prontas (ou ao menos com assinatura combinada) antes de FASE22-IMPL-03/04 as reaproveitarem nos novos campos de CPF/telefone secundário; estrutura de campo de endereço (FASE22-IMPL-03/04) combinada antes de FASE22-IMPL-05 poder ligar o autocomplete a ela.
