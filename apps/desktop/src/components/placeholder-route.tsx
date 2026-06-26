interface PlaceholderRouteProps {
  name: string;
}

export function PlaceholderRoute({ name }: PlaceholderRouteProps) {
  return (
    <div className="flex h-full items-center justify-center">
      <p className="text-lg text-muted-foreground">Fixly — {name}</p>
    </div>
  );
}
