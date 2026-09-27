---
name: run
description: Rodar o app LotIAdo (backend + mobile) de verdade — web e nativo (Android emulator) — para validar uma tarefa antes de considerá-la pronta
type: automatic
---

# Rodar o LotIAdo de verdade

Regra do projeto (ver `CLAUDE.md`): toda task que mexe em tela (mobile ou backoffice web) só está pronta depois de rodar o app de verdade, não só passar type-check/testes. Isso inclui o **emulador Android nativo**, não só `expo start --web` — telas com componentes nativos (ex. `@maplibre/maplibre-react-native`) não aparecem na web, e regressões de bundling (ex. incompatibilidade de lib com o Metro) só aparecem rodando de verdade.

## Setup (uma vez por máquina)

Guia completo, com os comandos de instalação do zero: [docs/guia-rodar-android-nativo.md](../../../docs/guia-rodar-android-nativo.md). Resumo:
- JDK 17 + Android SDK (cmdline-tools, platform-tools, emulator, platform 35, build-tools 35.0.0, system image `android-35;google_apis;x86_64`) instalados por usuário em `%USERPROFILE%\dev-tools\` (sem admin).
- AVD `lotiado_pixel` (Pixel 6, Android 35).
- Cada dev/máquina instala a própria cópia — não é compartilhado nem versionado no repo.

## Rodar

1. **Infra + backend**: `docker compose up -d` (raiz do repo) → `cd backend && alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &`
2. **Web** (mais rápido, cobre a maior parte das telas do backoffice): `cd mobile && npx expo start --web --port 8081`. Sem exceção — nunca alegue limitação técnica para pular a captura de tela; resolva o bloqueio (shim, seed de dados, etc.) antes.
3. **Nativo Android** (obrigatório para telas com módulo nativo, ex. mapa; recomendado ao final de toda task de UI):
   - Emulador: exporte as variáveis de `guia-rodar-android-nativo.md`, `emulator -avd lotiado_pixel -no-audio -no-boot-anim -gpu host &` (`-gpu swiftshader_indirect` pode renderizar tela preta em algumas GPUs — ver "armadilhas" no guia), espere `adb shell getprop sys.boot_completed` = `1`. Depois de abrir o app, espere ~15–20s (compilação de shader/fonte no emulador frio) antes de `screencap` — não capture cedo demais achando que travou.
   - Primeira vez (ou depois de mexer em módulo nativo/dependência): `npx expo prebuild --platform android` + `EXPO_PUBLIC_API_URL=http://10.0.2.2:8000 npx expo run:android` (build Gradle, ~10 min na 1ª vez — rode em background).
   - Depois do 1º build: `npx expo start --dev-client` basta para iterar em JS.
   - Screenshot: `adb exec-out screencap -p > shot.png`. Navegação: `adb shell input tap X Y` / `input text "..."` / `input keyevent 4` (voltar) / `am start -a android.intent.action.VIEW -d "lotiado://<rota>"` (deep link).

## Ao final de toda task que mexe em tela

1. Rodar web e nativo com dados de teste reais (seed via API ou `scripts/seed_user.py`).
2. Capturar screenshot de cada tela nova/alterada nas duas plataformas quando a tela existir nas duas; quando for específica de uma plataforma (ex. editor de mapa é só web — ver decisão de escopo do backlog), documentar isso explicitamente em vez de simular.
3. Screenshots vão em `docs/design/screenshots/` e são referenciados na seção **Evidências** do PR (ver skill `create-pr`).
4. Se algo quebrar só em nativo (ex. lib incompatível com Metro/Gradle), o fix entra na mesma task — não adiar para depois.
