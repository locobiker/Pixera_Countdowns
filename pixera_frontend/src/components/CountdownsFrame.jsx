import React, { useMemo } from "react";
import CountdownList from "./CountdownList";

/**
 * CountdownsFrame
 * Displays a scrollable list of countdowns, filtered and limited.
 * Handles filtering, sorting, and limiting — delegates rendering to CountdownList.
 */
export default function CountdownsFrame({ countdowns, filter, displayCount }) {
  // Apply filter and sort logic
  const filtered = useMemo(() => {
    if (!Array.isArray(countdowns)) return [];

    let list = countdowns;

    // Filter by cue name prefix
    if (filter === "A_") {
      list = list.filter((c) => c.cueName?.startsWith("A_"));
    }

    // Sort by time remaining (soonest first)
    list = [...list].sort((a, b) => a.totalMs - b.totalMs);

    // Limit visible items
    return list.slice(0, displayCount);
  }, [countdowns, filter, displayCount]);

  return (
    <div className="flex flex-col bg-white shadow-inner rounded-2xl p-4 border border-gray-200 max-h-[70vh] overflow-y-auto">
      <CountdownList countdowns={filtered} />
    </div>
  );
}