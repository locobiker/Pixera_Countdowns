import React from "react";
import { Wifi, WifiOff } from "lucide-react";

/**
 * TitleFrame
 * Displays project name and connection status.
 */
export default function TitleFrame({ projectName, connected }) {
  return (
    <div className="px-4 py-3 bg-gray-800 border-b border-gray-700 text-xl font-semibold">
      {connected ? (
        <Wifi className="text-green-500 w-6 h-6" />
      ) : (
        <WifiOff className="text-red-500 w-6 h-6" />
      )}
      <h1 className="text-2xl font-semibold tracking-tight">
        {projectName || "Unnamed Project"}
      </h1>
      <span
        className={`ml-4 text-sm font-medium ${
          connected ? "text-green-600" : "text-red-600"
        }`}
      >
        {connected ? "Connected" : "Disconnected"}
      </span>
    </div>
  );
}
