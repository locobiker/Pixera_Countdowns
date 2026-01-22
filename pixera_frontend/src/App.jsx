import React from "react";
import CountdownList from "./components/CountdownList";
import TitleFrame from "./components/TitleFrame";
import ControlFrame from "./components/ControlFrame";

export default function App() {
  const [connected, setConnected] = React.useState(false);
  const [projectName, setProjectName] = React.useState("Unnamed Project");
  const [countdownsRaw, setCountdownsRaw] = React.useState([]);
  const [filterMode, setFilterMode] = React.useState("all");
  const [timelineFilter, setTimelineFilter] = React.useState("running"); // "running" or specific timeline name
  const [displayCount, setDisplayCount] = React.useState(10);
  const [pollingEnabled, setPollingEnabled] = React.useState(false);
  const [isToggling, setIsToggling] = React.useState(false);

  // Fetch initial polling state
  React.useEffect(() => {
    const fetchPollingState = async () => {
      try {
        // const response = await fetch(`http://${window.location.hostname}:8000/api/polling/state`);
        const response = await fetch(`/api/polling/state`);
        if (response.ok) {
          const data = await response.json();
          setPollingEnabled(data.enabled || false);
        }
      } catch (error) {
        console.error("Failed to fetch polling state:", error);
      }
    };
    fetchPollingState();
  }, []);

  React.useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${window.location.host}/ws`;
    
    console.log("Attempting WebSocket connection to:", wsUrl); 
    
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => {
      console.log("WebSocket connected");
      setConnected(true);
    };
    
    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setConnected(false);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setConnected(false);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("WebSocket message received:", data);

        if (data.projectName) {
          setProjectName(data.projectName);
        }
        if (data.countdowns) {
          // Accept countdowns even if not an array initially, will be filtered later
          setCountdownsRaw(Array.isArray(data.countdowns) ? data.countdowns : []);
        }
        // Update polling state from WebSocket messages
        if (data.polling !== undefined) {
          setPollingEnabled(data.polling.enabled || false);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error, event.data);
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  // Compute list of unique timeline names for the combobox
  const availableTimelines = React.useMemo(() => {
    if (!Array.isArray(countdownsRaw)) return [];
    const names = new Set();
    for (const c of countdownsRaw) {
      if (c && typeof c.timelineName === "string" && c.timelineName.trim() !== "") {
        names.add(c.timelineName);
      }
    }
    return Array.from(names).sort((a, b) => a.localeCompare(b));
  }, [countdownsRaw]);

  // Handle polling toggle
  const handlePollingToggle = async () => {
    setIsToggling(true);
    try {
      const endpoint = pollingEnabled ? "disable" : "enable";
      //const url = `http://${window.location.hostname}:8000/api/polling/${endpoint}`;
      const url = `/api/polling/${endpoint}`;

      console.log("Toggling polling:", url);
      
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("Polling toggle response:", data);
        setPollingEnabled(data.polling?.enabled || false);
      } else {
        const errorText = await response.text();
        console.error("Failed to toggle polling:", response.status, errorText);
        alert(`Failed to toggle polling: ${response.status} ${errorText}`);
      }
    } catch (error) {
      console.error("Error toggling polling:", error);
      alert(`Error toggling polling: ${error.message}`);
    } finally {
      setIsToggling(false);
    }
  };

  // Process + sort countdowns
  const countdowns = React.useMemo(() => {
    // Hide countdowns when polling is disabled
    if (!pollingEnabled) {
      return [];
    }

    // Ensure countdownsRaw is an array
    if (!Array.isArray(countdownsRaw)) {
      return [];
    }

    try {
      let items = countdownsRaw
        .filter(c => c && c.id) // Filter out invalid items
        .map(c => ({
          cueHandle: c.id,
          name: c.cueName || "",
          type: c.cueType || "",
          note: c.note || "",
          totalMs: c.totalMs || 0,
          timelineName: c.timelineName || "",
          timelineMode: (c.timelineMode || "").toLowerCase()
        }));

      // Apply timeline filter
      if (timelineFilter === "running") {
        // Only show cues whose timeline is currently in "play" mode
        items = items.filter(c => c.timelineMode === "play");
      } else if (timelineFilter && timelineFilter !== "all") {
        // Show all countdowns from the selected timeline
        items = items.filter(c => c.timelineName === timelineFilter);
      }

      // Filtering - only apply if name exists and is a string
      if (filterMode === "A_") {
        items = items.filter(c => c.name && typeof c.name === 'string' && c.name.startsWith("A_"));
      }

      // Sort by closest finishing
      items.sort((a, b) => (a.totalMs || 0) - (b.totalMs || 0));

      // Limit displayed number - ensure displayCount is a valid positive number
      const validDisplayCount = Number.isInteger(displayCount) && displayCount > 0 ? displayCount : 10;
      return items.slice(0, validDisplayCount);
    } catch (error) {
      console.error("Error processing countdowns:", error);
      return [];
    }
  }, [countdownsRaw, filterMode, displayCount, pollingEnabled, timelineFilter]);

  return (
  <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col">
      <TitleFrame projectName={projectName} connected={connected} />

      <ControlFrame
        displayCount={displayCount}
        onDisplayCountChange={setDisplayCount}
        filterMode={filterMode}
        onFilterModeChange={setFilterMode}
        timelineFilter={timelineFilter}
        onTimelineFilterChange={setTimelineFilter}
        availableTimelines={availableTimelines}
        pollingEnabled={pollingEnabled}
        onPollingToggle={handlePollingToggle}
        isToggling={isToggling}
      />

      <div className="flex-1 overflow-y-auto px-4 py-2">
        {pollingEnabled ? (
          <CountdownList countdowns={countdowns} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>Polling is disabled. Enable polling to view countdowns.</p>
          </div>
        )}
      </div>
    </div>
  );
}
