import { Platform, useWindowDimensions } from 'react-native';

export const DESKTOP_BREAKPOINT = 900;

/** true só no navegador com janela larga: aí o app troca a bottom nav pela sidebar do WebShell. */
export function useIsDesktop(): boolean {
  const { width } = useWindowDimensions();
  return Platform.OS === 'web' && width >= DESKTOP_BREAKPOINT;
}
