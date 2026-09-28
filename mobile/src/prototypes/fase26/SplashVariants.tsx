import { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';
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

import { colors, fonts } from '../../theme/tokens';

/**
 * FASE26-IMPL-01 (SCRUM-252) — protótipos isolados de entrada do logo, além do
 * fade+scale já existente em mobile/src/components/SplashAnimation.tsx (não
 * alterado por este ticket). Referências pedidas pelo usuário: entrada divertida
 * tipo iFood, e efeito de "montagem com clique" tipo logo do Nintendo Switch
 * (sem som, é só a peça encaixando visualmente).
 */

const MARK_SIZE = 72;

const WORD_LETTERS = 'LotIAdo'.split('');

function CascadeLetter({ letter, index }: { letter: string; index: number }) {
  const opacity = useSharedValue(0);
  const translate = useSharedValue(10);
  const delay = 220 + index * 55;

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

/** Variação D — iFood-style: entrada elástica com leve overshoot + wordmark em cascata letra a letra. */
export function SplashBouncyEntrance({ onFinish }: { onFinish?: () => void }) {
  const markScale = useSharedValue(0.4);
  const markRotate = useSharedValue(-8);

  useEffect(() => {
    markScale.value = withSpring(1, { damping: 7, stiffness: 140 });
    markRotate.value = withSequence(
      withTiming(6, { duration: 220, easing: Easing.out(Easing.cubic) }),
      withSpring(0, { damping: 6, stiffness: 120 }),
    );

    const total = 220 + WORD_LETTERS.length * 55 + 500;
    const timer = setTimeout(() => onFinish?.(), total);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const markStyle = useAnimatedStyle(() => ({
    transform: [{ scale: markScale.value }, { rotate: `${markRotate.value}deg` }],
  }));

  return (
    <View style={styles.container}>
      <Animated.View style={markStyle}>
        <Svg width={MARK_SIZE} height={MARK_SIZE} viewBox="0 0 40 40">
          <Rect x={3} y={3} width={34} height={34} rx={7} fill={colors.primary} />
          <Path d="M3 20h34M20 3v34" stroke={colors.primaryForeground} strokeWidth={2} strokeOpacity={0.6} />
          <Rect x={22} y={22} width={12} height={12} rx={2} fill={colors.accent} />
        </Svg>
      </Animated.View>
      <View style={styles.wordRow}>
        {WORD_LETTERS.map((letter, i) => (
          <CascadeLetter key={i} letter={letter} index={i} />
        ))}
      </View>
    </View>
  );
}

/** Variação E — Nintendo Switch-style: peças do mark se encaixam em sequência com um "punch" de escala, sem som. */
export function SplashAssemble({ onFinish }: { onFinish?: () => void }) {
  const borderScale = useSharedValue(0);
  const crossOpacity = useSharedValue(0);
  const accentTranslate = useSharedValue(30);
  const accentScale = useSharedValue(0.3);
  const punch = useSharedValue(1);
  const wordOpacity = useSharedValue(0);

  useEffect(() => {
    borderScale.value = withTiming(1, { duration: 260, easing: Easing.out(Easing.cubic) });
    crossOpacity.value = withDelay(260, withTiming(0.6, { duration: 180 }));

    accentTranslate.value = withDelay(
      460,
      withSequence(
        withTiming(0, { duration: 180, easing: Easing.in(Easing.cubic) }),
        withTiming(0, { duration: 0 }),
      ),
    );
    accentScale.value = withDelay(460, withTiming(1, { duration: 180, easing: Easing.in(Easing.cubic) }));

    // "clique" visual: punch de escala no instante em que a peça encaixa.
    punch.value = withDelay(
      640,
      withSequence(
        withTiming(1.18, { duration: 70, easing: Easing.out(Easing.cubic) }),
        withSpring(1, { damping: 5, stiffness: 260 }),
      ),
    );

    wordOpacity.value = withDelay(820, withTiming(1, { duration: 260 }));

    const timer = setTimeout(() => onFinish?.(), 1500);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const borderStyle = useAnimatedStyle(() => ({ transform: [{ scale: borderScale.value }] }));
  const crossStyle = useAnimatedStyle(() => ({ opacity: crossOpacity.value }));
  const accentStyle = useAnimatedStyle(() => ({
    opacity: accentScale.value,
    transform: [
      { translateX: accentTranslate.value },
      { translateY: accentTranslate.value },
      { scale: accentScale.value },
    ],
  }));
  const punchStyle = useAnimatedStyle(() => ({ transform: [{ scale: punch.value }] }));
  const wordStyle = useAnimatedStyle(() => ({ opacity: wordOpacity.value }));

  return (
    <View style={styles.container}>
      <Animated.View style={punchStyle}>
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
      </Animated.View>
      <Animated.Text style={[styles.word, wordStyle]}>
        Lot
        <Text style={{ color: colors.primary }}>IA</Text>
        do
      </Animated.Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
    gap: 12,
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
  word: {
    fontFamily: fonts.displayBold,
    fontSize: 34,
    letterSpacing: -0.3,
    color: colors.foreground,
  },
});
