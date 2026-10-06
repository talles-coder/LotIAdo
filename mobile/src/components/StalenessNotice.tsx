import { StyleProp, StyleSheet, Text, View, ViewStyle } from 'react-native';
import { WifiOff } from 'lucide-react-native';

import { useIsOnline } from '../lib/useIsOnline';
import { formatRelativeTime } from '../lib/relativeTime';
import { colors, fonts } from '../theme/tokens';

interface StalenessNoticeProps {
  /** `dataUpdatedAt` do(s) `useQuery` da tela — 0 quando ainda não há nenhum dado, nem em cache. */
  updatedAt: number;
  style?: StyleProp<ViewStyle>;
}

/** Aviso de "dado pode estar desatualizado", mostrado só quando offline e a tela exibe dados vindos do cache local. */
export function StalenessNotice({ updatedAt, style }: StalenessNoticeProps) {
  const isOnline = useIsOnline();
  if (isOnline || !updatedAt) return null;

  return (
    <View style={[styles.container, style]}>
      <WifiOff size={13} color={colors.mutedForeground} />
      <Text style={styles.text}>Sem conexão — última atualização {formatRelativeTime(updatedAt)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  text: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.mutedForeground,
  },
});
