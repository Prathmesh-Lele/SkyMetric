import Link from "next/link";
import { Plane } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center gap-4 text-center">
      <div className="rounded-full bg-primary/10 p-4">
        <Plane className="h-8 w-8 text-primary" />
      </div>
      <div>
        <p className="text-5xl font-bold text-muted-foreground font-mono">404</p>
        <h2 className="text-lg font-semibold mt-2">Turbulence — page not found</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          This route isn&apos;t on our 10-corridor map.
        </p>
      </div>
      <Link
        href="/"
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
