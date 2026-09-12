import { Badge } from "@fixly/ui";

interface ModelIndicatorProps {
  model?: string;
  backend?: string;
}

export function ModelIndicator({
  model = "qwen2-0.5b",
  backend = "local",
}: ModelIndicatorProps) {
  const isLocal = backend === "local";

  return (
    <Badge
      variant={isLocal ? "secondary" : "outline"}
      className="text-[10px] cursor-default"
      title={`Running on ${backend}: ${model}`}
    >
      <span
        className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${
          isLocal ? "bg-emerald-500" : "bg-blue-500"
        }`}
      />
      {isLocal ? "Local" : "Cloud"} · {model}
    </Badge>
  );
}
