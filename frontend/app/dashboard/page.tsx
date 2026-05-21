import { getWorkspaceKnowledgeBase, getWorkspaces } from "@/lib/api"

async function loadKnowledgeBase() {
  try {
    const workspaces = await getWorkspaces()
    if (!workspaces.length) {
      return { workspaces, knowledgeBase: null }
    }

    return {
      workspaces,
      knowledgeBase: await getWorkspaceKnowledgeBase(workspaces[0].id),
    }
  } catch {
    return { workspaces: [], knowledgeBase: null }
  }
}

export default async function DashboardPage() {
  const { workspaces, knowledgeBase } = await loadKnowledgeBase()
  const documents = knowledgeBase?.documents ?? []
  const concepts = knowledgeBase?.cross_document_concepts ?? []

  return (
    <main className="min-h-screen bg-background px-6 py-8 text-foreground">
      <section className="mx-auto max-w-6xl">
        <div className="flex flex-col gap-2 border-b border-border pb-6">
          <p className="text-sm font-medium uppercase text-muted-foreground">
            Knowledge base
          </p>
          <h1 className="text-3xl font-semibold">
            {knowledgeBase?.workspace.title ?? "Subject workspaces"}
          </h1>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-md border border-border bg-card p-5">
            <p className="text-sm text-muted-foreground">Workspaces</p>
            <p className="mt-2 text-3xl font-semibold">{workspaces.length}</p>
          </div>
          <div className="rounded-md border border-border bg-card p-5">
            <p className="text-sm text-muted-foreground">Documents</p>
            <p className="mt-2 text-3xl font-semibold">{documents.length}</p>
          </div>
          <div className="rounded-md border border-border bg-card p-5">
            <p className="text-sm text-muted-foreground">Shared concepts</p>
            <p className="mt-2 text-3xl font-semibold">{concepts.length}</p>
          </div>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_1.2fr]">
          <section className="rounded-md border border-border">
            <div className="border-b border-border px-4 py-3 text-sm font-medium text-muted-foreground">
              Documents
            </div>
            {documents.length ? (
              documents.map((document) => (
                <div key={document.id} className="border-b border-border px-4 py-4 last:border-b-0">
                  <p className="font-medium">{document.title}</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {document.subject ?? "No subject"} · {document.status}
                  </p>
                </div>
              ))
            ) : (
              <p className="px-4 py-10 text-sm text-muted-foreground">
                Create a workspace and attach processed documents to build a
                multi-document knowledge base.
              </p>
            )}
          </section>

          <section className="rounded-md border border-border">
            <div className="border-b border-border px-4 py-3 text-sm font-medium text-muted-foreground">
              Cross-document concepts
            </div>
            {concepts.length ? (
              concepts.map((concept) => (
                <div key={concept.canonical_key} className="border-b border-border px-4 py-4 last:border-b-0">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-medium">{concept.label}</p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {concept.document_count} documents · {concept.node_count} nodes
                      </p>
                    </div>
                    <span className="rounded-sm border border-border px-2 py-1 text-xs text-muted-foreground">
                      merge candidate
                    </span>
                  </div>
                  {concept.descriptions[0] ? (
                    <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">
                      {concept.descriptions[0]}
                    </p>
                  ) : null}
                </div>
              ))
            ) : (
              <p className="px-4 py-10 text-sm text-muted-foreground">
                Shared concept candidates appear after two or more documents in a
                workspace contain matching graph nodes.
              </p>
            )}
          </section>
        </div>
      </section>
    </main>
  )
}
