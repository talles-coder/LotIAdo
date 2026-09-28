import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { router, usePathname } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Activity, Home, LogOut, Map, UserCog, UserPlus, Users } from 'lucide-react-native';

import { obterUsuarioAtual } from '../api/auth';
import { clearSession, useSession } from '../auth/session';
import { useIsDesktop } from '../lib/useIsDesktop';
import { colors, fonts } from '../theme/tokens';
import { Logo } from './Logo';

const NAV = [
  { href: '/home', label: 'Início', icon: Home },
  { href: '/loteamentos', label: 'Loteamentos', icon: Map },
  { href: '/clientes/novo', label: 'Novo cliente', icon: UserPlus },
  { href: '/corretores', label: 'Corretores', icon: Users },
  { href: '/usuarios', label: 'Usuários', icon: UserCog },
  { href: '/backoffice', label: 'Métricas de IA', icon: Activity },
] as const;

const CONTENT_MAX_WIDTH = 1120;

/**
 * Layout de site para o navegador em tela larga (backoffice, FASE5): sidebar fixa + barra
 * superior + conteúdo centralizado. Em janela estreita (ou sem sessão, ex.: login) devolve as
 * telas como estão, no formato mobile.
 */
export function WebShell({ children }: { children: ReactNode }) {
  const desktop = useIsDesktop();
  const token = useSession();
  const pathname = usePathname();

  if (!desktop || !token || pathname === '/login' || pathname === '/') {
    return <>{children}</>;
  }

  return (
    <View style={styles.root}>
      <Sidebar pathname={pathname} />
      <View style={styles.main}>
        <TopBar />
        <View style={styles.contentOuter}>
          <View style={styles.content}>{children}</View>
        </View>
      </View>
    </View>
  );
}

function Sidebar({ pathname }: { pathname: string }) {
  return (
    <View style={styles.sidebar}>
      <View style={styles.sidebarLogo}>
        <Logo size="md" onDark />
      </View>
      <View style={styles.navList}>
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Pressable
              key={href}
              onPress={() => router.push(href)}
              style={(state) => [
                styles.navItem,
                active && styles.navItemActive,
                !active && (state as { hovered?: boolean }).hovered && styles.navItemHover,
              ]}
            >
              <Icon size={18} color={active ? colors.primaryForeground : colors.earthForeground} />
              <Text style={[styles.navLabel, active && styles.navLabelActive]}>{label}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

function TopBar() {
  const meQuery = useQuery({ queryKey: ['auth', 'me'], queryFn: obterUsuarioAtual });
  const nome = meQuery.data?.full_name ?? meQuery.data?.email ?? '';
  const iniciais = nome
    .split(/[\s@.]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join('');

  async function handleLogout() {
    await clearSession();
    router.replace('/login');
  }

  return (
    <View style={styles.topBar}>
      <Text style={styles.topBarTitle}>Backoffice</Text>
      <View style={styles.topBarUser}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{iniciais || '?'}</Text>
        </View>
        <Text style={styles.userName}>{nome}</Text>
        <Pressable onPress={handleLogout} style={styles.logout} hitSlop={8}>
          <LogOut size={18} color={colors.mutedForeground} />
          <Text style={styles.logoutText}>Sair</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, flexDirection: 'row', backgroundColor: colors.background },
  sidebar: { width: 240, backgroundColor: colors.earth, paddingVertical: 24, paddingHorizontal: 16 },
  sidebarLogo: { paddingHorizontal: 8, marginBottom: 32 },
  navList: { gap: 4 },
  navItem: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 11, paddingHorizontal: 12, borderRadius: 10 },
  navItemActive: { backgroundColor: colors.primary },
  navItemHover: { backgroundColor: 'rgba(249, 244, 238, 0.08)' },
  navLabel: { fontFamily: fonts.bodyMedium, fontSize: 14, color: colors.earthForeground },
  navLabelActive: { color: colors.primaryForeground },
  main: { flex: 1 },
  topBar: {
    height: 64,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 32,
    backgroundColor: colors.card,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  topBarTitle: { fontFamily: fonts.display, fontSize: 18, color: colors.foreground },
  topBarUser: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatar: { width: 34, height: 34, borderRadius: 17, backgroundColor: colors.earth, alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontFamily: fonts.bodySemiBold, fontSize: 12, color: colors.earthForeground },
  userName: { fontFamily: fonts.body, fontSize: 14, color: colors.foreground },
  logout: { flexDirection: 'row', alignItems: 'center', gap: 6, marginLeft: 8 },
  logoutText: { fontFamily: fonts.body, fontSize: 14, color: colors.mutedForeground },
  contentOuter: { flex: 1, alignItems: 'center' },
  content: { flex: 1, width: '100%', maxWidth: CONTENT_MAX_WIDTH },
});
