import React from "react";
import CountdownFrame from "./CountdownFrame";

/**
 * CountdownList.jsx
 *
 * - countdowns: array of { cueHandle, name, totalMs, timelineName }
 *
 * Behavior:
 * - Keeps a local 'active' list so we don't re-add expired items sent by backend.
 * - When an item signals expiration (via onExpire prop or window event),
 *   we mark it as exiting (so it can run its collapse animation) and remove it
 *   only after the animation duration.
 * - The container uses transition rules to give a smooth upward motion for remaining items.
 */

const EXIT_ANIMATION_MS = 600; // should match CountdownFrame's CSS/JS duration

export default function CountdownList({ countdowns }) {
  const [active, setActive] = React.useState(countdowns || []);
  const [exiting, setExiting] = React.useState(() => new Set());
  const containerRef = React.useRef(null);

  // Apply backend updates - Pixera data is the source of truth
  // Backend updates always override local state, including timer values
  React.useEffect(() => {
    // Ensure countdowns is an array (default to empty array if not)
    const safeCountdowns = Array.isArray(countdowns) ? countdowns : [];

    setActive((prev) => {
      // Build map for quick lookup of existing items
      const prevMap = new Map(prev.map((p) => [p.cueHandle, p]));
      
      // For each incoming countdown from backend, use the backend data as source of truth
      // Only update if data actually changed to prevent unnecessary re-renders
      const updated = safeCountdowns.map((c) => {
        // Skip invalid items
        if (!c || !c.cueHandle) return null;
        
        const existing = prevMap.get(c.cueHandle);
        // Only create new object if data changed (check all relevant fields)
        if (existing && 
            existing.totalMs === c.totalMs &&
            existing.name === c.name &&
            existing.note === c.note &&
            existing.timelineName === c.timelineName &&
            existing.type === c.type &&
            existing.timelineMode === c.timelineMode) {
          return existing; // Reuse existing object to prevent re-render
        }
        return { ...c };
      }).filter(Boolean); // Remove any null entries from invalid items

      // Also keep any previously active items that are not in incoming only if they are currently exiting.
      // This prevents items from disappearing mid-animation
      const stillExiting = prev.filter((p) => 
        p && 
        p.cueHandle && 
        !updated.some((m) => m.cueHandle === p.cueHandle) && 
        exiting.has(p.cueHandle)
      );
      
      // Only update state if something actually changed
      const newActive = [...updated, ...stillExiting];
      
      // Deep comparison to avoid unnecessary updates
      if (newActive.length !== prev.length) {
        return newActive;
      }
      
      // Check if any items actually changed
      const hasChanges = newActive.some((item, idx) => {
        const prevItem = prev[idx];
        if (!prevItem || !item) return prevItem !== item;
        return prevItem.cueHandle !== item.cueHandle ||
               prevItem.totalMs !== item.totalMs ||
               prevItem.name !== item.name ||
               prevItem.note !== item.note ||
               prevItem.timelineName !== item.timelineName;
      });
      
      if (!hasChanges) {
        return prev; // No changes, return previous state
      }
      
      return newActive;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [countdowns]);

  // Handler used when a CountdownFrame tells us it's expired (preferred)
  const handleExpire = React.useCallback((cueHandle) => {
    // Mark as exiting so its component can apply collapse classes if needed
    setExiting((s) => new Set(s).add(cueHandle));

    // After animation finishes, remove the item from 'active'
    setTimeout(() => {
      setActive((prev) => prev.filter((c) => c.cueHandle !== cueHandle));
      setExiting((s) => {
        const n = new Set(s);
        n.delete(cueHandle);
        return n;
      });
    }, EXIT_ANIMATION_MS + 20); // small buffer
  }, []);

  // Back-compat: listen for window event 'countdownExpired' if CountdownFrame dispatches it
  React.useEffect(() => {
    const handler = (e) => {
      const cueHandle = e?.detail;
      if (!cueHandle) return;
      handleExpire(cueHandle);
    };
    window.addEventListener("countdownExpired", handler);
    return () => window.removeEventListener("countdownExpired", handler);
  }, [handleExpire]);

  // Render
  return (
    <div
      ref={containerRef}
      className="w-full flex flex-col gap-2" // 'gap' animates better than space-y for reflow
      style={{
        transition: `all ${Math.max(200, EXIT_ANIMATION_MS / 3)}ms ease`,
      }}
    >
      {active.map((c) => {
        // Skip invalid items
        if (!c || !c.cueHandle) return null;
        
        return (
          <CountdownFrame
            key={c.cueHandle}
            cueHandle={c.cueHandle}
            name={c.name}
            type={c.type}
            note={c.note}
            totalMs={c.totalMs}
            timelineName={c.timelineName}
            timelineMode={c.timelineMode}
            // pass onExpire so CountdownFrame can call this directly after its own animation
            onExpire={() => handleExpire(c.cueHandle)}
            // inform frame whether it's in exiting state (optional; frame can ignore)
            isExiting={exiting.has(c.cueHandle)}
          />
        );
      })}
    </div>
  );
}
