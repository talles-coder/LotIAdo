import { StyleSheet, Text, View } from 'react-native';
import { TextInput, type TextInputProps } from 'react-native-paper';

import { colors, fonts, radius } from '../theme/tokens';

/** Campo com label acima do input (não flutuante) + hint opcional abaixo — ver `Field` em clientes.novo.tsx no repo de referência do Lovable. */
export function Field({ label, hint, ...props }: { label: string; hint?: string } & TextInputProps) {
  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        mode="outlined"
        style={styles.input}
        outlineStyle={styles.outline}
        placeholderTextColor={colors.mutedForeground}
        {...props}
      />
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: 6,
  },
  label: {
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    color: colors.foreground,
  },
  input: {
    backgroundColor: colors.card,
  },
  outline: {
    borderRadius: radius.md,
  },
  hint: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.mutedForeground,
  },
});
