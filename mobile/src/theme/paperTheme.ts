import { MD3LightTheme } from 'react-native-paper';

import { colors, fonts, radius } from './tokens';

const fontConfig = {
  fontFamily: fonts.body,
} as const;

export const paperTheme = {
  ...MD3LightTheme,
  roundness: radius.md,
  fonts: {
    ...MD3LightTheme.fonts,
    default: fontConfig,
    displayLarge: { ...MD3LightTheme.fonts.displayLarge, fontFamily: fonts.displayBold },
    displayMedium: { ...MD3LightTheme.fonts.displayMedium, fontFamily: fonts.displayBold },
    displaySmall: { ...MD3LightTheme.fonts.displaySmall, fontFamily: fonts.display },
    headlineLarge: { ...MD3LightTheme.fonts.headlineLarge, fontFamily: fonts.displayBold },
    headlineMedium: { ...MD3LightTheme.fonts.headlineMedium, fontFamily: fonts.display },
    headlineSmall: { ...MD3LightTheme.fonts.headlineSmall, fontFamily: fonts.display },
    titleLarge: { ...MD3LightTheme.fonts.titleLarge, fontFamily: fonts.display },
    titleMedium: { ...MD3LightTheme.fonts.titleMedium, fontFamily: fonts.bodySemiBold },
    titleSmall: { ...MD3LightTheme.fonts.titleSmall, fontFamily: fonts.bodySemiBold },
    labelLarge: { ...MD3LightTheme.fonts.labelLarge, fontFamily: fonts.bodySemiBold },
    labelMedium: { ...MD3LightTheme.fonts.labelMedium, fontFamily: fonts.bodyMedium },
    labelSmall: { ...MD3LightTheme.fonts.labelSmall, fontFamily: fonts.bodyMedium },
    bodyLarge: { ...MD3LightTheme.fonts.bodyLarge, fontFamily: fonts.body },
    bodyMedium: { ...MD3LightTheme.fonts.bodyMedium, fontFamily: fonts.body },
    bodySmall: { ...MD3LightTheme.fonts.bodySmall, fontFamily: fonts.body },
  },
  colors: {
    ...MD3LightTheme.colors,
    primary: colors.primary,
    onPrimary: colors.primaryForeground,
    primaryContainer: colors.primarySoft,
    onPrimaryContainer: colors.primary,
    secondary: colors.secondary,
    onSecondary: colors.secondaryForeground,
    secondaryContainer: colors.secondary,
    onSecondaryContainer: colors.secondaryForeground,
    tertiary: colors.accent,
    onTertiary: colors.accentForeground,
    tertiaryContainer: colors.accentSoft,
    onTertiaryContainer: colors.accent,
    background: colors.background,
    onBackground: colors.foreground,
    surface: colors.card,
    onSurface: colors.foreground,
    surfaceVariant: colors.muted,
    onSurfaceVariant: colors.mutedForeground,
    outline: colors.border,
    outlineVariant: colors.input,
    error: colors.destructive,
    onError: colors.destructiveForeground,
  },
};
