export default function HomePage() {
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
      </section>
    </main>
  )
}
