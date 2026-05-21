import { LearningGraphView } from "@/components/graph/learning-graph-view"
import { getDocumentGraph, type LearningGraph } from "@/lib/api"

async function loadGraph(documentId: string) {
  try {
    return {
      graph: await getDocumentGraph(documentId),
      error: null,
    }
  } catch {
    return {
      graph: null,
      error: "Unable to load this document graph.",
    }
  }
}

export default async function GraphPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const result = await loadGraph(id)
  const graph: LearningGraph =
    result.graph ?? {
      document_id: id,
      nodes: [],
      edges: [],
      citations: [],
    }

  return (
    <main className="min-h-screen bg-background px-6 py-8 text-foreground">
      <section className="mx-auto max-w-7xl">
        <div className="flex flex-col gap-2 border-b border-border pb-6">
          <p className="text-sm font-medium uppercase text-muted-foreground">
            Learning graph
          </p>
          <h1 className="text-3xl font-semibold">Document {id}</h1>
          <p className="max-w-3xl text-sm text-muted-foreground">
            Inspect extracted knowledge nodes, learning relationships, and source
            citations from the Postgres graph.
          </p>
        </div>

        {result.error ? (
          <div className="mt-6 rounded-md border border-border px-5 py-4 text-sm text-muted-foreground">
            {result.error}
          </div>
        ) : null}

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-md border border-border p-4">
            <p className="text-sm text-muted-foreground">Nodes</p>
            <p className="mt-2 text-3xl font-semibold">{graph.nodes.length}</p>
          </div>
          <div className="rounded-md border border-border p-4">
            <p className="text-sm text-muted-foreground">Edges</p>
            <p className="mt-2 text-3xl font-semibold">{graph.edges.length}</p>
          </div>
          <div className="rounded-md border border-border p-4">
            <p className="text-sm text-muted-foreground">Citations</p>
            <p className="mt-2 text-3xl font-semibold">{graph.citations.length}</p>
          </div>
        </div>

        <LearningGraphView graph={graph} />
      </section>
    </main>
  )
}
