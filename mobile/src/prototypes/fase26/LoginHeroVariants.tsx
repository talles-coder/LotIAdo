import { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withRepeat,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import Svg, { Circle, Defs, Path, Pattern, Rect } from 'react-native-svg';

import { Logo } from '../../components/Logo';
import { colors } from '../../theme/tokens';

/**
 * FASE26-IMPL-01 (SCRUM-252) — protótipos isolados de animação sutil no hero da
 * tela de login. Nunca importado pela tela de login real (mobile/app/login.tsx).
 *
 * Divergência de domínio registrada (docs/design/lovable-mapeamento.md): o hero
 * do login não tem uma "foto de lotes" — usa um padrão SVG de grid que representa
 * terrenos subdivididos. As variações abaixo animam esse padrão, não uma imagem.
 */

const HERO_HEIGHT = 224;

function HeroFrame({ children }: { children: React.ReactNode }) {
  return (
    <View style={styles.hero}>
      {children}
      <Logo size="lg" onDark />
    </View>
  );
}

/** Variação A — paralaxe leve: o grid deriva devagar num loop infinito, sem parar. */
export function LoginHeroParallax() {
  const offset = useSharedValue(0);

  useEffect(() => {
    offset.value = withRepeat(
      withSequence(
        withTiming(10, { duration: 4000, easing: Easing.inOut(Easing.sin) }),
        withTiming(-10, { duration: 4000, easing: Easing.inOut(Easing.sin) }),
      ),
      -1,
    );
  }, [offset]);

  const style = useAnimatedStyle(() => ({
    transform: [{ translateX: offset.value }, { translateY: offset.value * 0.4 }],
  }));

  return (
    <HeroFrame>
      <Animated.View style={[StyleSheet.absoluteFill, style]}>
        <Svg width="130%" height="130%" opacity={0.15}>
          <Defs>
            <Pattern id="gridA" width={24} height={24} patternUnits="userSpaceOnUse">
              <Path d="M24 0H0V24" fill="none" stroke={colors.earthForeground} strokeWidth={1} />
            </Pattern>
          </Defs>
          <Rect width="100%" height="100%" fill="url(#gridA)" />
        </Svg>
      </Animated.View>
    </HeroFrame>
  );
}

/** Variação B — partículas discretas: pontos piscam em interseções do grid, como lotes "acendendo". */
const PARTICLE_POINTS = [
  { x: 40, y: 50, delay: 0 },
  { x: 120, y: 30, delay: 600 },
  { x: 220, y: 70, delay: 1200 },
  { x: 90, y: 110, delay: 300 },
  { x: 260, y: 40, delay: 900 },
  { x: 180, y: 120, delay: 1500 },
];

function Particle({ x, y, delay }: { x: number; y: number; delay: number }) {
  const opacity = useSharedValue(0);

  useEffect(() => {
    opacity.value = withDelay(
      delay,
      withRepeat(
        withSequence(
          withTiming(0.9, { duration: 900, easing: Easing.out(Easing.quad) }),
          withTiming(0, { duration: 1400, easing: Easing.in(Easing.quad) }),
        ),
        -1,
      ),
    );
  }, [delay, opacity]);

  const style = useAnimatedStyle(() => ({ opacity: opacity.value }));

  return (
    <Animated.View style={[styles.particle, { left: x, top: y }, style]}>
      <Svg width={10} height={10}>
        <Circle cx={5} cy={5} r={4} fill={colors.accentSoft} />
      </Svg>
    </Animated.View>
  );
}

export function LoginHeroParticles() {
  return (
    <HeroFrame>
      <View style={StyleSheet.absoluteFill}>
        <Svg style={StyleSheet.absoluteFill} width="100%" height="100%" opacity={0.15}>
          <Defs>
            <Pattern id="gridB" width={24} height={24} patternUnits="userSpaceOnUse">
              <Path d="M24 0H0V24" fill="none" stroke={colors.earthForeground} strokeWidth={1} />
            </Pattern>
          </Defs>
          <Rect width="100%" height="100%" fill="url(#gridB)" />
        </Svg>
        {PARTICLE_POINTS.map((p, i) => (
          <Particle key={i} {...p} />
        ))}
      </View>
    </HeroFrame>
  );
}

/** Variação C — pulse sutil: um "lote" do grid pulsa opacidade/escala, como um destaque. */
export function LoginHeroPulse() {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(0.5);

  useEffect(() => {
    scale.value = withRepeat(
      withSequence(
        withTiming(1.15, { duration: 1100, easing: Easing.inOut(Easing.quad) }),
        withTiming(1, { duration: 1100, easing: Easing.inOut(Easing.quad) }),
      ),
      -1,
    );
    opacity.value = withRepeat(
      withSequence(
        withTiming(0.9, { duration: 1100, easing: Easing.inOut(Easing.quad) }),
        withTiming(0.5, { duration: 1100, easing: Easing.inOut(Easing.quad) }),
      ),
      -1,
    );
  }, [opacity, scale]);

  const style = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ scale: scale.value }],
  }));

  return (
    <HeroFrame>
      <Svg style={StyleSheet.absoluteFill} width="100%" height="100%" opacity={0.15}>
        <Defs>
          <Pattern id="gridC" width={24} height={24} patternUnits="userSpaceOnUse">
            <Path d="M24 0H0V24" fill="none" stroke={colors.earthForeground} strokeWidth={1} />
          </Pattern>
        </Defs>
        <Rect width="100%" height="100%" fill="url(#gridC)" />
      </Svg>
      <Animated.View style={[styles.pulseLot, style]} />
    </HeroFrame>
  );
}

/**
 * Variação F — lote itinerante: um quadrado verde "preenche" uma célula do grid por vez,
 * pulando entre células diferentes da malha (não fica parado como em C). Ajuste pedido
 * pelo usuário (2026-09-28) sobre a C: em vez de pulsar no lugar, o destaque se move.
 */
const GRID_CELL = 24;
const WANDER_CELLS = [
  { col: 5, row: 1 },
  { col: 8, row: 2 },
  { col: 3, row: 3 },
  { col: 10, row: 1 },
  { col: 6, row: 4 },
  { col: 11, row: 3 },
] as const;
const WANDER_HOLD_MS = 900;
const WANDER_FADE_MS = 220;

export function LoginHeroWanderingLot() {
  const opacity = useSharedValue(0);
  const left = useSharedValue(WANDER_CELLS[0].col * GRID_CELL);
  const top = useSharedValue(WANDER_CELLS[0].row * GRID_CELL);

  useEffect(() => {
    let cancelled = false;
    let i = 0;

    function step() {
      if (cancelled) return;
      const cell = WANDER_CELLS[i % WANDER_CELLS.length];
      left.value = cell.col * GRID_CELL;
      top.value = cell.row * GRID_CELL;
      opacity.value = withSequence(
        withTiming(0.85, { duration: WANDER_FADE_MS, easing: Easing.out(Easing.quad) }),
        withDelay(WANDER_HOLD_MS, withTiming(0, { duration: WANDER_FADE_MS, easing: Easing.in(Easing.quad) })),
      );
      i++;
      timer = setTimeout(step, WANDER_FADE_MS * 2 + WANDER_HOLD_MS + 120);
    }

    let timer = setTimeout(step, 200);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const style = useAnimatedStyle(() => ({
    opacity: opacity.value,
    left: left.value,
    top: top.value,
  }));

  return (
    <HeroFrame>
      <Svg style={StyleSheet.absoluteFill} width="100%" height="100%" opacity={0.15}>
        <Defs>
          <Pattern id="gridF" width={GRID_CELL} height={GRID_CELL} patternUnits="userSpaceOnUse">
            <Path d="M24 0H0V24" fill="none" stroke={colors.earthForeground} strokeWidth={1} />
          </Pattern>
        </Defs>
        <Rect width="100%" height="100%" fill="url(#gridF)" />
      </Svg>
      <Animated.View style={[styles.wanderLot, style]} />
    </HeroFrame>
  );
}

const styles = StyleSheet.create({
  hero: {
    height: HERO_HEIGHT,
    backgroundColor: colors.earth,
    justifyContent: 'flex-end',
    paddingHorizontal: 24,
    paddingBottom: 32,
    overflow: 'hidden',
  },
  particle: {
    position: 'absolute',
  },
  pulseLot: {
    position: 'absolute',
    left: 160,
    top: 60,
    width: 24,
    height: 24,
    borderRadius: 4,
    backgroundColor: colors.accent,
  },
  wanderLot: {
    position: 'absolute',
    width: GRID_CELL,
    height: GRID_CELL,
    backgroundColor: colors.accent,
  },
});
