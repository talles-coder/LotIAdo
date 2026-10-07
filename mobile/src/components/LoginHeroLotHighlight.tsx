import { useEffect } from 'react';
import { StyleSheet } from 'react-native';
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withSequence,
  withTiming,
} from 'react-native-reanimated';

import { colors } from '../theme/tokens';

/**
 * SCRUM-253 (FASE26-IMPL-02) — destaque animado no grid do hero de login: um
 * quadrado verde do tamanho de uma célula da malha (mesmo grid 24×24 do padrão
 * SVG em mobile/app/login.tsx) pula entre células diferentes, "preenchendo" uma
 * célula por vez. Variação F aprovada pelo usuário (2026-09-28) — ver GIF em
 * docs/design/screenshots/scrum-252-fase26-F-lote-itinerante.gif.
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
const HOLD_MS = 900;
const FADE_MS = 220;

export function LoginHeroLotHighlight() {
  const opacity = useSharedValue(0);
  const left = useSharedValue(WANDER_CELLS[0].col * GRID_CELL);
  const top = useSharedValue(WANDER_CELLS[0].row * GRID_CELL);

  useEffect(() => {
    let cancelled = false;
    let i = 0;
    let timer: ReturnType<typeof setTimeout>;

    function step() {
      if (cancelled) return;
      const cell = WANDER_CELLS[i % WANDER_CELLS.length];
      left.value = cell.col * GRID_CELL;
      top.value = cell.row * GRID_CELL;
      opacity.value = withSequence(
        withTiming(0.85, { duration: FADE_MS, easing: Easing.out(Easing.quad) }),
        withDelay(HOLD_MS, withTiming(0, { duration: FADE_MS, easing: Easing.in(Easing.quad) })),
      );
      i++;
      timer = setTimeout(step, FADE_MS * 2 + HOLD_MS + 120);
    }

    timer = setTimeout(step, 200);
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

  return <Animated.View style={[styles.lot, style]} />;
}

const styles = StyleSheet.create({
  lot: {
    position: 'absolute',
    width: GRID_CELL,
    height: GRID_CELL,
    backgroundColor: colors.accent,
  },
});
