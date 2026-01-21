import React from "react";

/**
 * ControlFrame
 * Provides user controls for filtering and display options.
 */
export default function ControlFrame({
  displayCount,
  onDisplayCountChange,
  filterMode,
  onFilterModeChange,
  timelineFilter,
  onTimelineFilterChange,
  availableTimelines,
  pollingEnabled,
  onPollingToggle,
  isToggling,
}) {
  // Local state for input value to allow intermediate invalid states while typing
  const [inputValue, setInputValue] = React.useState(String(displayCount));
  
  // Sync local state when displayCount prop changes externally
  React.useEffect(() => {
    setInputValue(String(displayCount));
  }, [displayCount]);
  
  const handleCountChange = (ev) => {
    const newValue = ev.target.value;
    setInputValue(newValue); // Always update local state to allow typing
    
    // Parse and validate
    if (newValue === "") {
      return; // Allow empty while typing
    }
    
    const v = parseInt(newValue, 10);
    // Only update parent state if we have a valid positive number
    if (!Number.isNaN(v) && v >= 0) {
      onDisplayCountChange(v);
    }
  };
  
  const handleBlur = () => {
    // When user leaves the field, ensure we have a valid value
    const v = parseInt(inputValue, 10);
    if (Number.isNaN(v) || v < 0) {
      // Reset to current displayCount if invalid
      setInputValue(String(displayCount));
    } else {
      // Ensure parent state matches the valid value
      onDisplayCountChange(v);
    }
  };
  return (
    <div className="flex flex-row items-center gap-4 px-4 py-2 bg-gray-800 border-b border-gray-700">

      {/* Enable/Disable Polling Button */}
      <button
        onClick={onPollingToggle}
        disabled={isToggling}
        className={`px-4 py-2 rounded font-medium transition-colors ${
          pollingEnabled
            ? "bg-red-600 hover:bg-red-700 text-white"
            : "bg-green-600 hover:bg-green-700 text-white"
        } disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        {isToggling ? "..." : pollingEnabled ? "Disable Polling" : "Enable Polling"}
      </button>

      {/* Polling Status Indicator */}
      <div className="flex items-center gap-2">
        <div
          className={`w-3 h-3 rounded-full ${
            pollingEnabled ? "bg-green-500" : "bg-gray-500"
          }`}
        />
        <span className="text-sm text-gray-300">
          {pollingEnabled ? "Polling Active" : "Polling Disabled"}
        </span>
      </div>

      {/* Filter Selector */}
      <label className="flex items-center gap-2">
        <span className="text-sm">Filter:</span>
        <select
          value={filterMode}
          onChange={(ev) => onFilterModeChange(ev.target.value)}
          className="bg-gray-700 text-gray-100 border border-gray-600 rounded px-2 py-1 focus:outline-none focus:ring focus:ring-blue-500"
        >
          <option value="all">All</option>
          <option value="A_">Cues starting with "A_"</option>
        </select>
      </label>

      {/* Timeline Selector */}
      <label className="flex items-center gap-2">
        <span className="text-sm">Timeline:</span>
        <select
          value={timelineFilter}
          onChange={(ev) => onTimelineFilterChange(ev.target.value)}
          className="bg-gray-700 text-gray-100 border border-gray-600 rounded px-2 py-1 focus:outline-none focus:ring focus:ring-blue-500"
        >
          <option value="running">Display Only Playing</option>
          {Array.isArray(availableTimelines) &&
            availableTimelines.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
        </select>
      </label>

      {/* Countdowns to Display */}
      <label className="flex items-center gap-2">
        
        <span className="text-sm">Countdowns to display:</span>
        <input
          type="number"
          value={inputValue}
          onChange={handleCountChange}
          onBlur={handleBlur}
          min={0}
          step={1}
          className="bg-gray-700 text-gray-100 border border-gray-600 rounded px-2 py-1 w-20 focus:outline-none focus:ring focus:ring-blue-500"
        />
      </label>

    </div>
  );
}
