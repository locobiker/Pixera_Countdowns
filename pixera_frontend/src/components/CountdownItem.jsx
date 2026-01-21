import React, { useEffect, useState } from "react";

export default function CountdownItem({ countdown }) {
  const { id, timelineName, cueName } = countdown;

  // Clone totalMs as local state for countdown ticking
  const [remaining, setRemaining] = useState(countdown.totalMs);

  // Debug log: ensure countdown ticks
  useEffect(() => {
    console.log(`🎨 Rendering countdown ${cueName}: ${remaining}ms remaining`);
  }, [remaining, cueName]);

  useEffect(() => {
    // Reset local timer when the backend updates this countdown
    setRemaining(countdown.totalMs);
  }, [countdown.totalMs]);

  useEffect(() => {
    if (remaining <= 0) return;

    const interval = setInterval(() => {
      setRemaining((prev) => Math.max(prev - 100, 0)); // tick down by 100ms
    }, 100);

    return () => clearInterval(interval);
  }, [remaining]);

  // Compute HMSF display
  const hours = Math.floor(remaining / 3600000);
  const minutes = Math.floor((remaining % 3600000) / 60000);
  const seconds = Math.floor((remaining % 60000) / 1000);
  const frames = Math.floor(((remaining % 1000) / 1000) * 60); // assuming 60fps (we can change later)

  const display = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}.${String(frames).padStart(2, "0")}`;

  // Determine background color
  let bg = "bg-gray-700";
  if (remaining <= 5000) bg = "bg-red-600";
  else if (remaining <= 10000) bg = "bg-yellow-500 text-black";

  // Progress bar (just visual)
  const initialTotal = countdown.totalMs || 1;
  const progress = ((initialTotal - remaining) / initialTotal) * 100;

  return (
    <div className={`rounded-lg p-4 shadow ${bg} transition-colors duration-200`}>
      <div className="text-xl font-semibold mb-2">
        {cueName} <span className="text-gray-300">({timelineName})</span>
      </div>

      <div className="text-4xl font-mono tracking-wide mb-3">
        {display}
      </div>

      <div className="w-full h-2 bg-black bg-opacity-30 rounded overflow-hidden">
        <div
          className="h-full bg-white transition-all duration-200"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
