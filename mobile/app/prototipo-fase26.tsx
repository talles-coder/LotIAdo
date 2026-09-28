import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { Button } from 'react-native-paper';

import {
  LoginHeroParallax,
  LoginHeroParticles,
  LoginHeroPulse,
} from '../src/prototypes/fase26/LoginHeroVariants';
import { SplashAssemble, SplashBouncyEntrance } from '../src/prototypes/fase26/SplashVariants';
import { colors, fonts } from '../src/theme/tokens';
import { shared } from '../src/theme/shared';

/**
 * SCRUM-252 (FASE26-IMPL-01) — tela de protótipo isolada, nunca linkada na navegação
 * real (BottomNav/login) e nunca importada pela tela de login de verdade. Existe só
 * pra gravar os GIFs de cada variação e o usuário aprovar uma antes de SCRUM-253.
 * Acesso manual pela URL: /prototipo-fase26.
 */

const HERO_VARIANTS = [
  { key: 'A', label: 'A — Paralaxe leve', Component: LoginHeroParallax },
  { key: 'B', label: 'B — Partículas discretas', Component: LoginHeroParticles },
  { key: 'C', label: 'C — Pulse sutil no lote', Component: LoginHeroPulse },
] as const;

const SPLASH_VARIANTS = [
  { key: 'D', label: 'D — Entrada divertida (tipo iFood)', Component: SplashBouncyEntrance },
  { key: 'E', label: 'E — Montagem com "clique" (tipo Switch)', Component: SplashAssemble },
] as const;

export default function PrototipoFase26() {
  const [activeHero, setActiveHero] = useState<(typeof HERO_VARIANTS)[number]['key']>('A');
  const [splashKey, setSplashKey] = useState(0);
  const [activeSplash, setActiveSplash] = useState<(typeof SPLASH_VARIANTS)[number]['key'] | null>(
    null,
  );

  const HeroComponent = HERO_VARIANTS.find((v) => v.key === activeHero)!.Component;
  const SplashComponent = activeSplash
    ? SPLASH_VARIANTS.find((v) => v.key === activeSplash)!.Component
    : null;

  function replaySplash(key: (typeof SPLASH_VARIANTS)[number]['key']) {
    setActiveSplash(key);
    setSplashKey((k) => k + 1);
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Protótipos Fase 26 (SCRUM-252)</Text>
      <Text style={styles.subtitle}>
        Não faz parte do app real. Usar só para gravar os GIFs de cada variação.
      </Text>

      <Text style={styles.section}>Hero da tela de login</Text>
      <View style={styles.heroPreview} testID="hero-preview">
        <HeroComponent />
      </View>
      <View style={styles.buttonRow}>
        {HERO_VARIANTS.map((v) => (
          <Button
            key={v.key}
            mode={activeHero === v.key ? 'contained' : 'outlined'}
            onPress={() => setActiveHero(v.key)}
            style={styles.button}
          >
            {v.label}
          </Button>
        ))}
      </View>

      <Text style={styles.section}>Entrada do logo (splash)</Text>
      <View style={styles.splashPreview} testID="splash-preview">
        {SplashComponent ? (
          <SplashComponent key={splashKey} onFinish={() => {}} />
        ) : (
          <Text style={styles.placeholder}>Toque num botão abaixo para tocar a variação.</Text>
        )}
      </View>
      <View style={styles.buttonRow}>
        {SPLASH_VARIANTS.map((v) => (
          <Button key={v.key} mode="outlined" onPress={() => replaySplash(v.key)} style={styles.button}>
            {v.label}
          </Button>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 24,
    gap: 16,
    backgroundColor: colors.background,
  },
  title: {
    fontFamily: fonts.display,
    fontSize: 22,
    color: colors.foreground,
  },
  subtitle: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
    marginBottom: 8,
  },
  section: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 15,
    color: colors.foreground,
    marginTop: 8,
  },
  heroPreview: {
    ...shared.cardSurface,
    overflow: 'hidden',
    padding: 0,
  },
  splashPreview: {
    ...shared.cardSurface,
    height: 220,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholder: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
  },
  buttonRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  button: {
    marginBottom: 4,
  },
});
