import { useEffect, useRef, useState } from "react";
import { fetchTaxonomy } from "../api";
import { useI18n } from "../i18n/I18nProvider";

function isTransportFailure(error: unknown): boolean {
  return error instanceof TypeError || (error instanceof Error && /fetch|network|failed/i.test(error.message));
}

export default function ConnectionBanner({ onReachable, retryMs = 5000 }: { onReachable?: () => void; retryMs?: number }) {
  const { t } = useI18n();
  const [reachable, setReachable] = useState(true);
  // Kept in refs so the polling effect never re-runs on parent re-renders (an inline
  // onReachable prop would otherwise reset the timer — and, combined with a refetch
  // inside the callback, loop the probe back-to-back).
  const onReachableRef = useRef(onReachable);
  onReachableRef.current = onReachable;
  const wasUnreachableRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        await fetchTaxonomy();
        if (cancelled) return;
        setReachable(true);
        // Fire only on the unreachable → reachable transition: recovery is when
        // stale screens need a refetch; steady-state ticks must not re-fetch.
        if (wasUnreachableRef.current) {
          wasUnreachableRef.current = false;
          onReachableRef.current?.();
        }
      } catch (error) {
        if (!cancelled && isTransportFailure(error)) {
          wasUnreachableRef.current = true;
          setReachable(false);
        }
      }
    };
    void check();
    const id = setInterval(() => { void check(); }, retryMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [retryMs]);

  if (reachable) return null;
  return (
    <div className="connection-banner" role="status">
      {t("conn.unreachable")} <span>{t("conn.retrying")}</span>
    </div>
  );
}
