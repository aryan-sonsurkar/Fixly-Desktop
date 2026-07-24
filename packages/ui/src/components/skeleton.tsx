import * as React from "react";
import { cn } from "../lib/utils";

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("relative overflow-hidden rounded-md bg-primary/10", className)} {...props}>
      <div className="absolute inset-0 animate-shimmer" />
    </div>
  );
}

export { Skeleton };
