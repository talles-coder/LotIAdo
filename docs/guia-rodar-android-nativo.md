# Guia — rodar o app mobile nativo (Android) em Windows, sem Android Studio

Para quem for capturar telas/validar o app em nativo. Testado em duas máquinas Windows 11 (16 GB RAM, WHPX ativo, sem admin) — Dev 1 em 2026-09-26, Dev 2 em 2026-09-27 — reproduzido do zero na segunda sem ajuste no procedimento.

## O que precisa estar instalado (fora do repo, por usuário/máquina — não é compartilhado entre devs)

Convenção: tudo em `%USERPROFILE%\dev-tools\` (instalação por usuário, sem admin). Cada dev instala na própria máquina; os caminhos abaixo variam com o usuário do Windows.

| Item | Caminho |
|---|---|
| JDK 17 (Temurin) | `%USERPROFILE%\dev-tools\jdk17` |
| Android SDK (cmdline-tools, platform-tools, emulator, platform 35, build-tools 35.0.0, system image `android-35;google_apis;x86_64`) | `%USERPROFILE%\dev-tools\android-sdk` |
| AVD | `lotiado_pixel` (Pixel 6, Android 35) |

O Java do sistema costuma ser o 8 — **sempre** exporte o JDK 17 na sessão, não dependa do `java` do PATH padrão. Se `dev-tools` ainda não existir nesta máquina, instale do zero:

```bash
mkdir -p "$USERPROFILE/dev-tools" && cd "$USERPROFILE/dev-tools"
curl -sL -o jdk17.zip "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse?project=jdk"
curl -sL -o cmdline-tools.zip "https://dl.google.com/android/repository/commandlinetools-win-13114758_latest.zip"
# Extrair (ex. via PowerShell Expand-Archive): jdk17.zip -> dev-tools/jdk17 (a pasta jdk-17.x dentro do zip vira "jdk17");
# cmdline-tools.zip -> dev-tools/android-sdk/cmdline-tools/latest (a pasta "cmdline-tools" dentro do zip é renomeada para "latest")
export JAVA_HOME="$USERPROFILE/dev-tools/jdk17"
export ANDROID_HOME="$USERPROFILE/dev-tools/android-sdk"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
yes | sdkmanager.bat --licenses
sdkmanager.bat "platform-tools" "platforms;android-35" "build-tools;35.0.0" "emulator" "system-images;android-35;google_apis;x86_64"
echo "no" | avdmanager.bat create avd -n lotiado_pixel -k "system-images;android-35;google_apis;x86_64" -d pixel_6
```

No Git Bash, os executáveis do `cmdline-tools/bin` são `.bat` — chame `sdkmanager.bat`/`avdmanager.bat` explicitamente (sem a extensão, o Bash não acha o comando no PATH).

## Variáveis de ambiente (por sessão de Bash)

```bash
export JAVA_HOME="$USERPROFILE/dev-tools/jdk17"
export ANDROID_HOME="$USERPROFILE/dev-tools/android-sdk"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
```

## Subir tudo

```bash
# 1. Infra: docker compose up -d (ver README/Makefile). Porta do Postgres é 5432 por padrão
#    (POSTGRES_PORT no .env se precisar mudar — ex. outro projeto já usando 5432 na máquina).
#    Migrations com o dono do schema:
cd backend
docker compose up -d   # a partir da raiz do repo
alembic upgrade head   # usa MIGRATIONS_DATABASE_URL/DATABASE_URL do backend/.env

# 2. API — 0.0.0.0 para o emulador alcançar; em nativo NÃO precisa de CORS
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 3. Emulador (espera o boot)
emulator -avd lotiado_pixel -no-audio -no-boot-anim -gpu swiftshader_indirect &
until [ "$(adb shell getprop sys.boot_completed | tr -d '\r')" = "1" ]; do sleep 5; done

# 4. Expo — o emulador enxerga o host em 10.0.2.2
cd ../mobile
EXPO_PUBLIC_API_URL=http://10.0.2.2:8000 CI=1 npx expo start --android --port 8081
```

O primeiro `expo start --android` baixa e instala o **Expo Go** no emulador sozinho; o bundle leva ~40 s. Confira a aceleração com `emulator -accel-check` (deve dizer "WHPX ... installed and usable").

## Dados de teste

```bash
cd backend
python -m scripts.seed_user --email mapa@test.com --password senha123 --tenant-slug mapa-demo
```

Depois, com o token de `POST /auth/login`, crie loteamento e lotes pela API (`POST /loteamentos`, `POST /loteamentos/{id}/lotes`, `PATCH /lotes/{id}/status`). **Não existe endpoint para gravar `lotes.geometria`** — preencha por SQL, definindo o tenant por causa do RLS:

```sql
BEGIN;
SELECT set_config('app.tenant_id', (SELECT id::text FROM tenants WHERE slug='mapa-demo'), true);
UPDATE lotes SET geometria = ST_GeomFromText('POLYGON((-46.6333 -23.5505,-46.6328 -23.5505,-46.6328 -23.5510,-46.6333 -23.5510,-46.6333 -23.5505))', 4326) WHERE id = '<id>';
COMMIT;
```

(`docker exec -i lotiado-postgres psql -U lotiado -d lotiado`). Transições de status: `disponivel → reservado → vendido`; não vai direto de `disponivel` a `vendido`.

## Dirigir o emulador pela linha de comando

```bash
adb exec-out screencap -p > shot.png        # screenshot (1080x2400; a Read tool mostra em 900x2000 → multiplique coords por 1.2)
adb shell input tap X Y                     # toque (coords da tela real, 1080x2400)
adb shell input text "texto"                # digitar (sem espaços; ok para email/senha)
adb shell input keyevent 4                  # voltar / fecha teclado
adb shell am start -a android.intent.action.VIEW -d "exp://10.0.2.2:8081/--/loteamentos/<id>/mapa"   # deep link para uma rota
```

Armadilhas vistas:
- Na primeira abertura aparece o **menu do desenvolvedor** do Expo Go cobrindo a tela — toque em "Continue" antes de interagir; o primeiro toque em campos costuma ser engolido por ele.
- Toque no campo, espere ~1–2 s, e só então `input text`.
- O botão flutuante "Tools" do Expo Go aparece nos prints; feche/ignore ou recorte.
- Login de teste: `mapa@test.com` / `senha123` (tenant `mapa-demo`).
- **Tela preta sólida ao abrir o app (status bar ok, conteúdo RN preto)**: visto com `-gpu swiftshader_indirect` numa GPU NVIDIA via WHPX — trocar para `-gpu host` resolveu. Se persistir mesmo com `-gpu host`, é só demora: a 1ª compilação de shader/fonte custom (`@expo-google-fonts/*`) no emulador frio pode levar **15–20 s** depois do splash nativo sumir — espere mais antes de `screencap`, não assuma que travou.

## Mapa: precisa de development build (não roda no Expo Go)

O mapa usa MapLibre + tiles do OpenStreetMap (decisão D10): **sem conta e sem chave de API**, mas o módulo é nativo, então o Expo Go não serve para a tela de mapa. Gere e instale um development build no emulador:

```bash
cd mobile
npx expo prebuild --platform android      # gera mobile/android (ignorado pelo git)
EXPO_PUBLIC_API_URL=http://10.0.2.2:8000 npx expo run:android   # compila (~10 min na 1ª vez) e instala no emulador
```

Precisa de `JAVA_HOME` (JDK 17) e `ANDROID_HOME` exportados e do emulador já de pé. Depois do 1º build, `npx expo start --dev-client` basta para iterar em JS. Deep link: `lotiado://loteamentos/<id>/mapa`.

## Web (Expo for Web, SCRUM-74)

O target web agora é oficial (`react-native-web` nas dependências, `WebShell.web.tsx` com sidebar em tela larga, `tokenStorage.web.ts` com `localStorage`, `LoteamentoMap.web.tsx` como stand-in até FASE5-IMPL-03):
- `cd mobile && EXPO_PUBLIC_API_URL=http://localhost:8000 npx expo start --web --port 8081`;
- o backend libera CORS para `localhost:8081`/`19006` (`cors_origins` em `app/config.py`; sobrescreva via `CORS_ORIGINS` no `.env`);
- Playwright (Python) para dirigir o navegador; use `page.locator("input")` em vez de `get_by_label` (o Paper duplica o label).

iOS não é possível nesta máquina (Windows).
