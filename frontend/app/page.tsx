import { getHealthUrl } from "@/lib/api"

async function getBackendStatus() {
  try {
    const response = await fetch(getHealthUrl(), {
      cache: "no-store",
    })

    if (!response.ok) {
      return "offline"
    }

    const data = (await response.json()) as { status?: string }
    return data.status === "ok" ? "online" : "offline"
  } catch {
    return "offline"
  }
}

export default async function HomePage() {
  const backendStatus = await getBackendStatus()
  const isOnline = backendStatus === "online"

  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-16">
        <p className="text-sm font-medium uppercase tracking-widest text-muted-foreground">
          AI Learning OS
        </p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight">
          Knowledge graph learning workspace
        </h1>
        <p className="mt-4 max-w-2xl text-muted-foreground">
          Rebuild skeleton is ready. The next milestone is the foundation pipeline:
          upload, parse, chunk, extract, and render a learning graph with source citations.
        </p>
        <div className="mt-8 flex w-fit items-center gap-3 rounded-md border px-4 py-3 text-sm">
          <span
            className={`h-2.5 w-2.5 rounded-full ${
              isOnline ? "bg-emerald-500" : "bg-destructive"
            }`}
          />
          <span className="font-medium">Backend API is {backendStatus}</span>
        </div>
      </section>
    </main>
  )
}
