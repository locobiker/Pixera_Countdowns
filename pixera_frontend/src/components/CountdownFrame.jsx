import React from "react";

/**
 * CountdownFrame
 *
 * Props:
 * - cueHandle: string
 * - name: string
 * - totalMs: number (backend-reported)
 * - timelineName: string (optional)
 * - onExpire: function(cueHandle) => void  // called once, after exit animation
 * - isExiting: boolean (optional) // parent can inform frame it's exiting
 * - disableAutoTimer: boolean (optional) // if true, only backend controls timer (no local ticking)
 *
 * Behavior:
 * - If disableAutoTimer is false: Local frontend owns ticking. Backend updates only applied if backend value
 *   changed substantially from the last backend value (not every tick).
 * - If disableAutoTimer is true: Only backend controls the countdown, no local timer ticking.
 * - When local remaining hits 0, we start an exit animation and call onExpire
 *   after EXIT_MS so the parent can remove the item.
 */

const EXIT_MS = 600;
// Set to true to disable automatic frontend timer - backend will fully control countdown
const DISABLE_AUTO_TIMER = true;

const CountdownFrame = React.memo(function CountdownFrame({
  cueHandle,
  name,
  type,
  note,
  totalMs = 0,
  timelineName,
  timelineMode,
  onExpire,
  isExiting: parentExiting = false,
  disableAutoTimer = DISABLE_AUTO_TIMER,
}) {
  const [remaining, setRemaining] = React.useState(totalMs ?? 0);
  const [exiting, setExiting] = React.useState(false);
  const [hasStarted, setHasStarted] = React.useState(false);

  // Keep track of the last backend value we've seen, so repeated identical
  // websocket messages don't force unnecessary resyncs.
  const lastBackendRef = React.useRef(totalMs ?? 0);

  // A ref so we call onExpire only once
  const expiredCalledRef = React.useRef(false);

  // Use a ref to track if timer should be running (checked inside interval)
  const shouldTickRef = React.useRef(false);

  // Apply backend updates immediately - Pixera data is the source of truth
  // If disableAutoTimer is true, only backend controls the countdown (no local ticking)
  React.useEffect(() => {
    // Clamp negative values to 0 for display (backend should handle this, but safety check)
    const safeTotalMs = Math.max(0, totalMs ?? 0);
    
    // Only update state if the value actually changed to avoid unnecessary re-renders
    setRemaining((prev) => {
      if (prev !== safeTotalMs) {
        return safeTotalMs;
      }
      return prev;
    });
    
    if (disableAutoTimer) {
      // Backend-only mode: no local timer, just display backend value
      lastBackendRef.current = safeTotalMs;
      
      // Reset expired/exiting states if value is positive (only if changed)
      if (safeTotalMs > 0 && exiting) {
        expiredCalledRef.current = false;
        setExiting(false);
      }
      return;
    }
    
    // Auto-timer mode: local timer logic (original behavior)
    const lastBackend = lastBackendRef.current ?? 0;
    
    // Don't start timer if original value is negative (shouldn't happen if backend is correct)
    if ((totalMs ?? 0) < 0) {
      setHasStarted(false);
      shouldTickRef.current = false;
      lastBackendRef.current = safeTotalMs;
      return;
    }
    
    // Determine if countdown is actively decreasing
    if (safeTotalMs !== lastBackend && lastBackend > 0) {
      // Countdown value changed from a previous non-zero value
      if (safeTotalMs < lastBackend && safeTotalMs >= 0) {
        // Countdown decreased - cue is actively running, start/continue timer
        setHasStarted(true);
        shouldTickRef.current = true;
      } else if (safeTotalMs > lastBackend) {
        // Countdown increased (cue was reset/restarted), stop the timer
        setHasStarted(false);
        shouldTickRef.current = false;
      }
    } else if (safeTotalMs === lastBackend && lastBackend > 0) {
      // Countdown stayed the same (and we have a previous value) - pause the timer
      // This means the countdown has paused/stopped in Pixera
      setHasStarted(false);
      shouldTickRef.current = false;
    } else if (safeTotalMs === lastBackend && lastBackend === 0) {
      // Both are 0 - initial state, don't start timer
      setHasStarted(false);
      shouldTickRef.current = false;
    }
    
    // Update the last backend value
    lastBackendRef.current = safeTotalMs;
    
    // If backend value is positive and we were exiting/expired, reset those states
    // This handles cases where a cue is restarted in Pixera
    if (safeTotalMs > 0) {
      expiredCalledRef.current = false;
      setExiting(false);
    }
  }, [totalMs, disableAutoTimer]);

  // Update the ref when hasStarted changes (only in auto-timer mode)
  React.useEffect(() => {
    if (!disableAutoTimer) {
      shouldTickRef.current = hasStarted;
    }
  }, [hasStarted, disableAutoTimer]);

  // Only start ticking interval when the countdown has started (decreased from backend)
  // The interval checks shouldTickRef to ensure it stops when paused
  // This effect is skipped entirely if disableAutoTimer is true
  React.useEffect(() => {
    if (disableAutoTimer || !hasStarted) {
      // Clear any existing interval if auto-timer is disabled or we're pausing
      return;
    }

    const id = setInterval(() => {
      // Check the ref to see if we should still be ticking
      if (!shouldTickRef.current) {
        return;
      }
      
      setRemaining((r) => {
        if (r <= 0) return 0;
        return r - 100;
      });
    }, 100);

    return () => clearInterval(id);
  }, [hasStarted, disableAutoTimer]);

  // When remaining hits zero, trigger exit and call onExpire after EXIT_MS
  React.useEffect(() => {
    if (remaining > 0) return;

    // Start exiting (visual collapse)
    if (!exiting) setExiting(true);

    // Safety: ensure onExpire is called only once per lifecycle
    if (!expiredCalledRef.current) {
      expiredCalledRef.current = true;

      // give the animation time to play, then notify parent to remove
      const t = setTimeout(() => {
        try {
          if (typeof onExpire === "function") onExpire(cueHandle);
          // also dispatch a window event for backward compatibility
          window.dispatchEvent(new CustomEvent("countdownExpired", { detail: cueHandle }));
        } catch (err) {
          console.warn("onExpire error:", err);
        }
      }, EXIT_MS + 10);

      return () => clearTimeout(t);
    }
  }, [remaining, exiting, cueHandle, onExpire]);

  // If parent tells us it's exiting, mirror that (useful if parent initiates removal)
  React.useEffect(() => {
    if (parentExiting && !exiting) setExiting(true);
  }, [parentExiting, exiting]);

  // Formatting
  const formatTime = (ms) => {
    const totalSeconds = Math.max(0, Math.floor(ms / 1000));
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const deci = Math.floor((ms % 1000) / 100);
    return `${minutes}:${seconds.toString().padStart(2, "0")}.${deci}`;
  };

  // Memoize computed values to prevent unnecessary re-renders
  const timerColor = React.useMemo(() => {
    return remaining <= 3000 ? "bg-red-600" :
           remaining <= 10000 ? "bg-amber-600" :
           "bg-green-600";
  }, [remaining]);

  // Memoize container classes to prevent unnecessary re-renders
  const containerClasses = React.useMemo(() => {
    return `transition-all duration-600 overflow-hidden rounded-xl shadow-md border border-gray-200 ${timerColor}
      ${exiting ? "opacity-0 max-h-0 p-0 mt-0" : "opacity-100 max-h-40 p-3"}
      w-1/2 mx-auto`;
  }, [timerColor, exiting]);

  // Memoize formatted time to prevent unnecessary recalculations
  const formattedTime = React.useMemo(() => {
    const totalSeconds = Math.max(0, Math.floor(remaining / 1000));
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const deci = Math.floor((remaining % 1000) / 100);
    return `${minutes}:${seconds.toString().padStart(2, "0")}.${deci}`;
  }, [remaining]);

  return (
    <div className={containerClasses}>
      <div className="flex justify-between items-center">
        <div className="flex flex-col">
          <span className="text-lg font-semibold text-gray-900 whitespace-pre-line">{name}{type ? ` (Type: ${type})` : " (No Type)"}{note ? ` — ${note}` : ""}</span>
          {timelineName && <span className="text-sm text-gray-500">{timelineName}</span>}
        </div>

        <div className={`text-3xl font-bold tabular-nums`}>
          {formattedTime}
        </div>
      </div>
    </div>
  );
});

export default CountdownFrame;
