import { getNeo4jStatus } from "@/lib/api"

async function loadNeo4jStatus() {
  try {
    return await getNeo4jStatus()
  } catch {
    return null
  }
}

export default async function GraphPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const neo4jStatus = await loadNeo4jStatus()

  return (
    <main className="min-h-screen bg-background px-6 py-8 text-foreground">
      <section className="mx-auto max-w-6xl">
        <div className="flex flex-col gap-2 border-b border-border pb-6">
          <p className="text-sm font-medium uppercase text-muted-foreground">
            Learning graph
          </p>
          <h1 className="text-3xl font-semibold">Document {id}</h1>
        </div>

        <div className="mt-6 rounded-md border border-border bg-card p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-medium">Neo4j runtime</p>
              <p className="mt-2 text-sm text-muted-foreground">
                {neo4jStatus?.message ??
                  "Backend status is unavailable. The Postgres graph remains the system of record."}
              </p>
            </div>
            <span className="rounded-sm border border-border px-2 py-1 text-xs uppercase text-muted-foreground">
              {neo4jStatus?.state ?? "unknown"}
            </span>
          </div>
        </div>
      </section>
    </main>
  )
}
