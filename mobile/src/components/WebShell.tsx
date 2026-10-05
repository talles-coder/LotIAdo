import type { ReactNode } from 'react';

/** Nativo não tem shell: o layout web (sidebar + área central) vive em WebShell.web.tsx. */
export function WebShell({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
