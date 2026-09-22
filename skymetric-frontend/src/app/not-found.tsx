import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center gap-4 text-center">
      <p className="text-6xl font-bold text-muted-foreground">404</p>
      <div>
        <h2 className="text-lg font-semibold">Page not found</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          The page you&apos;re looking for doesn&apos;t exist.
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
