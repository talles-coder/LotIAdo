# Guia — rodar o app mobile nativo (Android) nesta máquina Windows

Para quem for capturar telas/validar o app em nativo sem Android Studio. Testado em 2026-09-26 (Windows 11, 16 GB RAM, WHPX ativo, sem admin).

## O que já está instalado (fora do repo)

Tudo em `C:\Users\User\dev-tools\` (instalação por usuário, sem admin):

| Item | Caminho |
|---|---|
| JDK 17 (Temurin) | `C:\Users\User\dev-tools\jdk17` |
| Android SDK (cmdline-tools, platform-tools, emulator, platform 35, build-tools 35.0.0, system image `android-35;google_apis;x86_64`) | `C:\Users\User\dev-tools\android-sdk` |
| AVD | `lotiado_pixel` (Pixel 6, Android 35) |

O Java do sistema é o 8 — **sempre** exporte o JDK 17 na sessão. Se a pasta `dev-tools` não existir (outra máquina), reinstale: baixe o JDK 17 zip (Adoptium) e o `commandlinetools-win` (Google), monte `android-sdk/cmdline-tools/latest`, rode `sdkmanager --licenses` e instale os pacotes da tabela, depois `avdmanager create avd -n lotiado_pixel -k "system-images;android-35;google_apis;x86_64" -d pixel_6`.

## Variáveis de ambiente (por sessão de Bash)

```bash
export JAVA_HOME=/c/Users/User/dev-tools/jdk17
export ANDROID_HOME=/c/Users/User/dev-tools/android-sdk
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
```

## Subir tudo

```bash
# 1. Infra + banco (ver README/Makefile). Nesta máquina o Postgres do LotIAdo está na porta 55499
#    (5432 é de outro projeto). Migrations com o dono do schema:
cd backend
export MIGRATIONS_DATABASE_URL=postgresql+asyncpg://lotiado:lotiado@localhost:55499/lotiado
alembic upgrade head

# 2. API — 0.0.0.0 para o emulador alcançar; em nativo NÃO precisa de CORS
export DATABASE_URL=postgresql+asyncpg://lotiado_app:lotiado_app@localhost:55499/lotiado
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

## Limitação conhecida: Google Maps no Expo Go

O **Expo Go não renderiza o mapa do Google** hoje: a chave embutida nele é rejeitada (`adb logcat | grep "Google Maps Android API"` mostra "Ensure that the Google Maps Android API v2 is enabled ... host.exp.exponent"). Resultado: o `MapView` aparece com fundo liso e logo "Google", **sem tiles e sem polígonos**. Para ver o mapa real é preciso:

1. Uma chave da Google Maps Platform com **Maps SDK for Android** habilitado (do dono do projeto — não criar por conta própria);
2. Configurá-la em `app.json` → `android.config.googleMaps.apiKey` (ou via `app.config.js` lendo env, sem commitar a chave);
3. Um **development build** (`npx expo prebuild --platform android` + `npx expo run:android`, usando o JDK/SDK acima), não o Expo Go.

Sem a chave, para PR use o stand-in web descartável descrito abaixo e diga isso no PR.

## Alternativa: captura via web (sem emulador)

Rota mais rápida para prints de telas que não dependem de biblioteca nativa (usada no SCRUM-70):
- `npm install --no-save react-native-web@~0.21.0` em `mobile/` (o `expo start --web` precisa dele);
- shims **descartáveis, nunca commitados**: `src/storage/tokenStorage.web.ts` (localStorage) e, se houver mapa, `src/components/LoteamentoMap.web.tsx` (stand-in SVG com as mesmas props);
- o backend não tem CORS: rode um wrapper local (`from app.main import app; app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8081"], ...)`) com `uvicorn cors_app:app --app-dir <pasta>` — **não** abra o Chrome com `--disable-web-security` (é bloqueado);
- Playwright (Python) + `C:\Program Files\Google\Chrome\Application\chrome.exe` com viewport 390x844 e `device_scale_factor=2`.

iOS não é possível nesta máquina (Windows).
