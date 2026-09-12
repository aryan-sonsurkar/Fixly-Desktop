import { useState, useEffect } from "react";
import { Badge } from "@fixly/ui";

export function OfflineIndicator() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return (
    <Badge
      variant={isOnline ? "default" : "destructive"}
      className="text-[10px] cursor-default"
    >
      <span
        className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${
          isOnline ? "bg-green-500" : "bg-red-500"
        }`}
      />
      {isOnline ? "Online" : "Offline"}
    </Badge>
  );
}
