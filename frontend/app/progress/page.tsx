import { getReviewQueue } from "@/lib/api"

async function loadQueue() {
  try {
    return await getReviewQueue()
  } catch {
    return null
  }
}

export default async function ProgressPage() {
  const queue = await loadQueue()
  const items = queue?.items ?? []
  const dueCount = items.length
  const weakCount = items.filter((item) => item.mastery.status === "weak").length
  const averageMastery = dueCount
    ? items.reduce((sum, item) => sum + item.mastery.mastery_score, 0) / dueCount
    : 0

  return (
    <main className="min-h-screen bg-background px-6 py-8 text-foreground">
      <section className="mx-auto max-w-6xl">
        <div className="flex flex-col gap-2 border-b border-border pb-6">
          <p className="text-sm font-medium uppercase text-muted-foreground">
            Spaced repetition
          </p>
          <h1 className="text-3xl font-semibold">Daily review queue</h1>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-md border border-border bg-card p-5">
            <p className="text-sm text-muted-foreground">Due now</p>
            <p className="mt-2 text-3xl font-semibold">{dueCount}</p>
          </div>
          <div className="rounded-md border border-border bg-card p-5">
            <p className="text-sm text-muted-foreground">Weak nodes</p>
            <p className="mt-2 text-3xl font-semibold">{weakCount}</p>
          </div>
          <div className="rounded-md border border-border bg-card p-5">
            <p className="text-sm text-muted-foreground">Average mastery</p>
            <p className="mt-2 text-3xl font-semibold">
              {Math.round(averageMastery * 100)}%
            </p>
          </div>
        </div>

        <div className="mt-6 overflow-hidden rounded-md border border-border">
          <div className="grid grid-cols-[1fr_120px_120px_120px] bg-secondary px-4 py-3 text-sm font-medium text-muted-foreground">
            <span>Node</span>
            <span>Status</span>
            <span>Priority</span>
            <span>Reviews</span>
          </div>
          {items.length ? (
            items.map((item) => (
              <div
                key={item.mastery.id}
                className="grid grid-cols-[1fr_120px_120px_120px] border-t border-border px-4 py-4 text-sm"
              >
                <div>
                  <p className="font-medium">{item.node_label}</p>
                  <p className="mt-1 line-clamp-1 text-muted-foreground">
                    {item.practice_item?.question ??
                      item.node_description ??
                      "Review this concept from its source material."}
                  </p>
                </div>
                <span className="capitalize">{item.mastery.status}</span>
                <span>{item.priority.toFixed(1)}</span>
                <span>{item.mastery.review_count}</span>
              </div>
            ))
          ) : (
            <div className="border-t border-border px-4 py-10 text-sm text-muted-foreground">
              No due reviews found. Connect Supabase and submit practice attempts
              to populate the queue.
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
