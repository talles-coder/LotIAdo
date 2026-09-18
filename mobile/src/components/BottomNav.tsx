import { Pressable, StyleSheet, Text, View } from 'react-native';
import { router, usePathname } from 'expo-router';
import { Home, Map, Monitor, UserPlus } from 'lucide-react-native';

import { colors, fonts } from '../theme/tokens';

const NAV = [
  { href: '/home', label: 'Início', icon: Home, enabled: true },
  { href: '/loteamentos', label: 'Loteamentos', icon: Map, enabled: true },
  { href: '/clientes/novo', label: 'Cliente', icon: UserPlus, enabled: true },
  { href: '/backoffice', label: 'Backoffice', icon: Monitor, enabled: false },
] as const;

/**
 * Nav inferior fixo (Início/Loteamentos/Cliente/Backoffice), igual ao `MobileShell` do
 * repo de referência do Lovable — ver docs/design/lovable-mapeamento.md. "Backoffice"
 * ainda não tem tela (Fase 5): fica visível mas desabilitado em vez de linkar pra uma
 * rota que não existe. "Cliente" (SCRUM-65) já linka para o cadastro de cliente.
 */
export function BottomNav() {
  const pathname = usePathname();

  return (
    <View style={styles.nav}>
      {NAV.map(({ href, label, icon: Icon, enabled }) => {
        const active = enabled && pathname.startsWith(href);
        return (
          <Pressable
            key={href}
            disabled={!enabled}
            onPress={() => router.push(href)}
            style={styles.item}
          >
            <View style={[styles.iconWrap, active && styles.iconWrapActive]}>
              <Icon size={20} color={active ? colors.primary : colors.mutedForeground} strokeWidth={2} />
            </View>
            <Text style={[styles.label, active && styles.labelActive, !enabled && styles.labelDisabled]}>
              {label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  nav: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.card,
  },
  item: {
    flex: 1,
    minHeight: 64,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingTop: 8,
    paddingBottom: 10,
  },
  iconWrap: {
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 4,
  },
  iconWrapActive: {
    backgroundColor: colors.primarySoft,
  },
  label: {
    fontFamily: fonts.bodyMedium,
    fontSize: 11,
    color: colors.mutedForeground,
  },
  labelActive: {
    color: colors.primary,
    fontFamily: fonts.bodySemiBold,
  },
  labelDisabled: {
    opacity: 0.5,
  },
});
