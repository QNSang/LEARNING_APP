export default async function GraphPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params

  return (
    <main className="min-h-screen p-8">
      <h1 className="text-2xl font-semibold">Learning Graph</h1>
      <p className="mt-2 text-muted-foreground">
        Graph workspace placeholder for document {id}.
      </p>
    </main>
  )
}
