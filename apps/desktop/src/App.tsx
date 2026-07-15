import { StartupGate } from "@/components/startup-screen";
import { AppProvider } from "@/providers/app-provider";

export default function App() {
  return (
    <StartupGate>
      <AppProvider />
    </StartupGate>
  );
}
