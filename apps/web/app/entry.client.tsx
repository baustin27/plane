import { startTransition, StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { HydratedRouter } from "react-router/dom";

// PLANEAGENT: Force client-side only rendering to avoid hydration issues
// This replaces hydrateRoot with createRoot, skipping SSR hydration
startTransition(() => {
  const container = document;
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <HydratedRouter />
    </StrictMode>
  );
});
