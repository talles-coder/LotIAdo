import { StyleSheet, Text, View } from 'react-native';
import Svg, { Path, Rect } from 'react-native-svg';

import { colors, fonts } from '../theme/tokens';

const SIZES = {
  sm: { mark: 28, text: 20 },
  md: { mark: 36, text: 24 },
  lg: { mark: 48, text: 34 },
} as const;

/** Marca: um terreno dividido em lotes. Ver docs/design/lovable-mapeamento.md. */
export function Logo({
  size = 'md',
  onDark = false,
}: {
  size?: keyof typeof SIZES;
  onDark?: boolean;
}) {
  const { mark, text } = SIZES[size];
  const wordColor = onDark ? colors.earthForeground : colors.foreground;

  return (
    <View style={styles.row}>
      <Svg width={mark} height={mark} viewBox="0 0 40 40">
        <Rect x={3} y={3} width={34} height={34} rx={7} fill={colors.primary} />
        <Path d="M3 20h34M20 3v34" stroke={colors.primaryForeground} strokeWidth={2} strokeOpacity={0.6} />
        <Rect x={22} y={22} width={12} height={12} rx={2} fill={colors.accent} />
      </Svg>
      <Text style={[styles.word, { fontSize: text, color: wordColor }]}>
        Lot
        <Text style={{ color: colors.primary }}>IA</Text>
        do
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  word: {
    fontFamily: fonts.displayBold,
    letterSpacing: -0.3,
  },
});
