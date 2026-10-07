import { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withSequence,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import Svg, { Path, Rect } from 'react-native-svg';

import { colors, fonts } from '../theme/tokens';

/**
 * Tela de abertura: a moldura + cruz do mark montam (estilo "encaixe" do Nintendo
 * Switch, sem som), a palavra "LotIAdo" cai em cascata letra a letra (estilo iFood),
 * e só depois o quadrado verde cai de fora do quadro e "bate" em cima do laranja.
 * Variação G aprovada pelo usuário (2026-09-28), SCRUM-253 (FASE26-IMPL-02) — GIF do
 * protótipo em docs/design/screenshots/scrum-252-fase26-G-splash-assemble-drop.gif.
 */

const MARK_SIZE = 72;
const WORD_LETTERS = 'LotIAdo'.split('');
const WORD_START_DELAY = 900;
const HOLD_AFTER_MS = 500;

function CascadeLetter({ letter, index }: { letter: string; index: number }) {
  const opacity = useSharedValue(0);
  const translate = useSharedValue(10);
  const delay = WORD_START_DELAY + index * 55;

  useEffect(() => {
    opacity.value = withDelay(delay, withTiming(1, { duration: 200 }));
    translate.value = withDelay(delay, withSpring(0, { damping: 8, stiffness: 180 }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const style = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ translateY: translate.value }],
  }));

  const isIA = letter === 'I' || letter === 'A';
  return (
    <Animated.Text style={[styles.letter, isIA && { color: colors.primary }, style]}>
      {letter}
    </Animated.Text>
  );
}

export function SplashAnimation({ onFinish }: { onFinish: () => void }) {
  const screenOpacity = useSharedValue(1);
  const borderScale = useSharedValue(0);
  const crossOpacity = useSharedValue(0);
  const accentTranslateY = useSharedValue(-90);
  const accentSquashY = useSharedValue(1);
  const accentSquashX = useSharedValue(1);

  useEffect(() => {
    borderScale.value = withTiming(1, { duration: 260, easing: Easing.out(Easing.cubic) });
    crossOpacity.value = withDelay(260, withTiming(0.6, { duration: 180 }));

    // queda do quadrado verde: acelera (gravidade) e "baque" (squash) na aterrissagem.
    accentTranslateY.value = withDelay(480, withTiming(0, { duration: 320, easing: Easing.in(Easing.quad) }));
    accentSquashY.value = withDelay(
      800,
      withSequence(
        withTiming(0.6, { duration: 70, easing: Easing.out(Easing.cubic) }),
        withSpring(1, { damping: 5, stiffness: 260 }),
      ),
    );
    accentSquashX.value = withDelay(
      800,
      withSequence(
        withTiming(1.35, { duration: 70, easing: Easing.out(Easing.cubic) }),
        withSpring(1, { damping: 5, stiffness: 260 }),
      ),
    );

    const total = WORD_START_DELAY + WORD_LETTERS.length * 55 + HOLD_AFTER_MS;
    screenOpacity.value = withDelay(total, withTiming(0, { duration: 320, easing: Easing.in(Easing.cubic) }));
    const timer = setTimeout(() => onFinish(), total + 320);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const screenStyle = useAnimatedStyle(() => ({ opacity: screenOpacity.value }));
  const borderStyle = useAnimatedStyle(() => ({ transform: [{ scale: borderScale.value }] }));
  const crossStyle = useAnimatedStyle(() => ({ opacity: crossOpacity.value }));
  const accentStyle = useAnimatedStyle(() => ({
    transform: [
      { translateY: accentTranslateY.value },
      { scaleY: accentSquashY.value },
      { scaleX: accentSquashX.value },
    ],
  }));

  return (
    <Animated.View style={[styles.container, screenStyle]} pointerEvents="none">
      <View style={{ width: MARK_SIZE, height: MARK_SIZE }}>
        <Animated.View style={[StyleSheet.absoluteFill, borderStyle]}>
          <Svg width={MARK_SIZE} height={MARK_SIZE} viewBox="0 0 40 40">
            <Rect x={3} y={3} width={34} height={34} rx={7} fill={colors.primary} />
          </Svg>
        </Animated.View>
        <Animated.View style={[StyleSheet.absoluteFill, crossStyle]}>
          <Svg width={MARK_SIZE} height={MARK_SIZE} viewBox="0 0 40 40">
            <Path d="M3 20h34M20 3v34" stroke={colors.primaryForeground} strokeWidth={2} />
          </Svg>
        </Animated.View>
        <Animated.View style={[StyleSheet.absoluteFill, accentStyle]}>
          <Svg width={MARK_SIZE} height={MARK_SIZE} viewBox="0 0 40 40">
            <Rect x={22} y={22} width={12} height={12} rx={2} fill={colors.accent} />
          </Svg>
        </Animated.View>
      </View>
      <View style={styles.wordRow}>
        {WORD_LETTERS.map((letter, i) => (
          <CascadeLetter key={i} letter={letter} index={i} />
        ))}
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFill,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    zIndex: 10,
  },
  wordRow: {
    flexDirection: 'row',
  },
  letter: {
    fontFamily: fonts.displayBold,
    fontSize: 34,
    letterSpacing: -0.3,
    color: colors.foreground,
  },
});
