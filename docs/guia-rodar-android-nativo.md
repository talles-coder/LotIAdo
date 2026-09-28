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

**Login com dados já existentes (evita gerar loteamento/lote na mão):** `user@test.com` / `senha123`, tenant `demo` — já tem loteamentos ("Residencial Teste Mapa", "Residencial Documentos Demo") e pelo menos 1 lote com geometria. Teste sempre com esse login primeiro; só rode o seed abaixo se precisar de um tenant novo/vazio de propósito.

```bash
cd backend
python -m scripts.seed_user --email mapa@test.com --password senha123 --tenant-slug mapa-demo
```

`mapa-demo` criado por esse comando **nasce vazio** (sem loteamentos) — não assuma que tem os mesmos dados de `demo` só porque o nome é parecido.

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
- **Tela preta e permanece preta com `npx expo run:android` (dev-client, não Expo Go)**: o log mostra `Opening lotiado://expo-development-client/?url=http%3A%2F%2F192.168.x.x%3APORT` (IP da LAN da máquina) em vez de `10.0.2.2` — o emulador não necessariamente alcança o IP da LAN do host (firewall/roteamento). Fix sem rebuildar nada:
  ```bash
  adb reverse tcp:PORT tcp:PORT
  adb shell am force-stop com.lotiado.mobile
  adb shell am start -a android.intent.action.VIEW -d "lotiado://expo-development-client/?url=http%3A%2F%2Flocalhost%3APORT"
  ```
  (troque `PORT` pela porta do Metro, ex. `8081`/`8082`). Depois disso o app carrega o bundle via `localhost` redirecionado pelo `adb reverse`.
- **Porta 8081 "in use"**: quase sempre é uma sessão anterior (sua ou de outro terminal) já servindo o mesmo repo — confira com `curl -s -o /dev/null -w "%{http_code}" http://localhost:8081` antes de subir outro `expo start` numa porta alternativa. Se responder 200, **reuse-a** (evita gasto de rebuild/CORS extra); só suba em outra porta se precisar rodar dois apps diferentes ao mesmo tempo.

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
- **use sempre a porta 8081** — o backend só libera CORS para `localhost:8081`/`19006` (`cors_origins` em `app/config.py`); subir em outra porta (ex. 8090) quebra toda chamada à API com erro de CORS silencioso no console do browser, não no terminal do Expo.
- `page.locator("input")` em vez de `get_by_label`/`getByLabel` (o Paper duplica o label) para preencher formulários por automação.

### Capturar screenshot web sem ferramenta de navegador interativa na sessão

Se a sessão não tiver Claude in Chrome / built-in browser conectado (comum em ambiente não-interativo), **não pule a evidência** — use Playwright headless via Node, que já roda sem setup extra nesta máquina (Chromium do Playwright já fica cacheado em `%LOCALAPPDATA%\ms-playwright` depois do primeiro uso):

```bash
# instale playwright num diretório fora do repo (nunca em mobile/package.json — não é dependência do app)
cd <scratchpad ou outra pasta temporária> && npm init -y >/dev/null && npm install playwright@1.63.0 --no-save
npx --yes playwright install chromium   # no-op se já estiver cacheado
```

Script mínimo (login real + navegação + screenshot):
```js
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await (await browser.newContext({ viewport: { width: 430, height: 900 } })).newPage();
  await page.goto('http://localhost:8081/login', { waitUntil: 'networkidle' });
  const inputs = await page.locator('input').all();
  await inputs[0].fill('user@test.com');
  await inputs[1].fill('senha123');
  await page.getByRole('button', { name: 'Entrar' }).click();
  await page.waitForTimeout(2000); // sem waitForURL — expo-router faz navegação client-side
  await page.goto('http://localhost:8081/loteamentos', { waitUntil: 'networkidle' });
  await page.screenshot({ path: 'shot.png' });
  await browser.close();
})();
```
Rode com `node script.js` a partir de `mobile/` (o `page.goto` para rotas do expo-router funciona bem em navegação direta; evite `waitForURL` depois de um clique que causa navegação client-side, pode nunca resolver — use `waitForTimeout` + `page.url()` para checar).

**Simular offline para telas com `useIsOnline`/`NetInfo`:** `context.setOffline(true)` sozinho **não é suficiente**. A implementação web do `@react-native-community/netinfo` prioriza a API `navigator.connection` (NetworkInformation) quando o browser suporta — e Chromium suporta — então ela escuta o evento `'change'` desse objeto, não `window online/offline`. Depois de `setOffline`, dispare manualmente:
```js
await page.evaluate(() => navigator.connection?.dispatchEvent(new Event('change')));
```
Sem isso, a UI simplesmente não reage (parece bug na feature, mas é só o teste que não notificou a lib).

iOS não é possível nesta máquina (Windows).

### Capturar GIF de uma animação (sem ferramenta de gravação de tela na sessão)

Mesmo cenário do item anterior, mas para uma **animação** (não uma tela estática) — caso de `FASE26-IMPL-01`. Sem `ffmpeg` nem gravador de tela disponíveis, a receita é: Playwright tira uma rajada de screenshots do elemento (não da página inteira — recorta melhor) em intervalo curto, e o Pillow (já disponível nesta máquina, `python -c "import PIL"`) monta o GIF a partir dos frames:

```js
// 1) rajada de frames com Playwright — screenshot de um locator específico (ex. testID
// virando data-testid no RN Web), não da página inteira, pra já vir recortado.
const target = page.locator('[data-testid="hero-preview"]');
await target.screenshot({ path: `frames/f000.png` });
await page.waitForTimeout(80); // repita em loop pela duração da animação
```
```python
# 2) monta o GIF com Pillow a partir dos frames em ordem
from PIL import Image
import glob
frames = [Image.open(p).convert('RGB') for p in sorted(glob.glob('frames/*.png'))]
frames[0].save('saida.gif', save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True)
```
Pontos de atenção: (1) o primeiro `page.goto` num Metro frio pode levar 2-3 min pra bundlar — use `timeout: 240000` no `page.goto`, o timeout padrão de 30s estoura; (2) screenshot de `locator` (elemento) em vez de `page` já recorta certo, sem precisar de crop depois; (3) ~10-15 frames num intervalo de 60-90ms já é suficiente pra um GIF de revisão assíncrona (não precisa de 30fps).
