import { useEffect, useRef } from 'react';
import { Animated, Easing, StyleSheet } from 'react-native';

import { Logo } from './Logo';
import { colors } from '../theme/tokens';

/**
 * Tela de abertura com o logo animado (fade + scale-in, segura um instante, fade-out),
 * tipo iFood/Nubank — o splash nativo (app.json) é só um fundo sólido; a marca "acontece" aqui.
 */
export function SplashAnimation({ onFinish }: { onFinish: () => void }) {
  const scale = useRef(new Animated.Value(0.85)).current;
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const screenOpacity = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.parallel([
        Animated.timing(logoOpacity, {
          toValue: 1,
          duration: 380,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
        Animated.spring(scale, {
          toValue: 1,
          friction: 6,
          tension: 60,
          useNativeDriver: true,
        }),
      ]),
      Animated.delay(450),
      Animated.timing(screenOpacity, {
        toValue: 0,
        duration: 320,
        easing: Easing.in(Easing.cubic),
        useNativeDriver: true,
      }),
    ]).start(() => onFinish());
  }, [logoOpacity, onFinish, scale, screenOpacity]);

  return (
    <Animated.View style={[styles.container, { opacity: screenOpacity }]} pointerEvents="none">
      <Animated.View style={{ opacity: logoOpacity, transform: [{ scale }] }}>
        <Logo size="lg" />
      </Animated.View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFill,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
});
