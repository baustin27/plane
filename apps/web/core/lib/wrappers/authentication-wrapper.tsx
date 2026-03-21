import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { observer } from "mobx-react";
// PLANEAGENT: Auth wrapper that allows rendering without waiting for auth
// This prevents hydration mismatches between server (no session) and client

type TAuthenticationWrapper = {
  children: ReactNode;
};

export const AuthenticationWrapper = observer(function AuthenticationWrapper(props: TAuthenticationWrapper) {
  const { children } = props;
  
  // PLANEAGENT: Always render children immediately
  // Auth state will be resolved client-side after hydration
  // This prevents SSR hydration mismatch
  return <>{children}</>;
});
