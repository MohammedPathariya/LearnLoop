import benchmarks from '../data/benchmarks.json';
import { MetricCard, PageHeader, StatusNotice } from '../components/UI';

function Benchmarks() {
  const load = benchmarks.load_test;
  return (
    <div className="page benchmark-page">
      <PageHeader
        technical
        eyebrow="Technical transparency"
        title="System benchmarks"
        description="Reproducible measurements for retrieval quality and local concurrency. These are engineering results, not learner progress."
        actions={<a className="button technical" href="https://github.com/MohammedPathariya/LearnLoop/tree/main/docs" target="_blank" rel="noreferrer">View reports</a>}
      />
      <StatusNotice type="info">
        <strong>Local evidence only.</strong> The load test ran with the client and backend sharing one Mac. It does not establish hosted production capacity.
      </StatusNotice>

      <section className="benchmark-section">
        <div className="section-heading">
          <div><p className="eyebrow technical-text">Retrieval quality</p><h2>Real project corpus</h2></div>
          <span>Updated {benchmarks.updated}</span>
        </div>
        <div className="benchmark-comparison">
          {benchmarks.retrieval.map((run) => (
            <article className="benchmark-run" key={run.name}>
              <div className="card-topline"><span className="badge technical">Measured</span><span>{run.hits} hits</span></div>
              <h3>{run.name}</h3>
              <div className="metric-grid compact">
                <MetricCard tone="technical" label="Recall" value={`${Math.round(run.recall * 100)}%`} />
                <MetricCard tone="technical" label="p50 latency" value={`${run.p50_ms} ms`} />
                <MetricCard tone="technical" label="p95 latency" value={`${run.p95_ms} ms`} />
              </div>
              <p>{run.documents} documents · {run.chunks} indexed chunks · query embedding and search only</p>
              <code>{run.source}</code>
            </article>
          ))}
        </div>
      </section>

      <section className="benchmark-section">
        <div className="section-heading">
          <div><p className="eyebrow technical-text">Concurrency</p><h2>500-user local load test</h2></div>
          <span className="badge technical">Passed locally</span>
        </div>
        <div className="metric-grid">
          <MetricCard tone="technical" label="Simulated users" value={load.users} />
          <MetricCard tone="technical" label="Requests" value={load.requests.toLocaleString()} />
          <MetricCard tone="technical" label="Failures" value={load.failures} />
          <MetricCard tone="technical" label="Throughput" value={`${load.rps} req/s`} />
          <MetricCard tone="technical" label="p50 latency" value={`${load.p50_ms} ms`} />
          <MetricCard tone="technical" label="p95 latency" value={`${load.p95_ms} ms`} />
        </div>
        <div className="methodology-card">
          <h3>Run context</h3>
          <dl>
            <div><dt>Server</dt><dd>{load.server}</dd></div>
            <div><dt>Database</dt><dd>{load.database}</dd></div>
            <div><dt>Environment</dt><dd>{load.environment}</dd></div>
            <div><dt>Provenance</dt><dd><code>{load.source}</code></dd></div>
          </dl>
        </div>
      </section>

      <section className="benchmark-section muted-benchmark">
        <p className="eyebrow technical-text">Generation reliability</p>
        <h2>Schema repair is implemented, but no rate is claimed yet.</h2>
        <p>Quiz and flashcard outputs are schema-validated with at most two repair retries. A public success percentage will appear only after a reproducible evaluation report exists.</p>
      </section>
    </div>
  );
}

export default Benchmarks;
