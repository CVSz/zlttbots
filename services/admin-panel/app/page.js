import SectionCard from '../components/SectionCard'

const partnerRows = [
  { partner: 'CreatorHub', clicks: 14222, conversions: 812, revenue: '$48,720', status: 'Healthy' },
  { partner: 'TrendNova', clicks: 9831, conversions: 461, revenue: '$28,110', status: 'Review' },
  { partner: 'ShopPulse', clicks: 12054, conversions: 733, revenue: '$41,980', status: 'Healthy' }
]

const approvalQueue = [
  { owner: 'Ops Team', asset: 'Top 5 gadgets under $30', slot: '13:00 UTC', state: 'Scheduled' },
  { owner: 'Creative Review', asset: 'UGC ad variant B', slot: '14:30 UTC', state: 'Needs approval' },
  { owner: 'Compliance', asset: 'Flash sale countdown', slot: '16:00 UTC', state: 'Approved' }
]

const edgeRoutes = [
  { host: 'api.zeaz.dev', service: 'Kong / nginx edge', control: 'Rate limited + WAF' },
  { host: 'admin.zeaz.dev', service: 'Admin dashboard', control: 'Cloudflare Access' },
  { host: 'predict.zeaz.dev', service: 'Viral predictor', control: 'JWT or service token' },
  { host: 'grafana.zeaz.dev', service: 'Monitoring', control: 'Internal only' }
]

const goLiveChecklist = [
  'Postgres backup and restore drill completed',
  'Cloudflare Access enabled for admin surfaces',
  'Approved affiliate hosts configured in click tracker',
  'Analytics summary and health endpoints returning data'
]

export default function HomePage() {
  return (
    <main className="dashboard-root">
      <header className="hero">
        <div>
          <p className="badge">Go-live</p>
          <h1>ZTTATO Operator Console</h1>
          <p>Unified operations for partner analytics, compliant redirect tracking, edge routing, and human-reviewed content workflows.</p>
        </div>
        <div className="hero-stats">
          <article>
            <span>Tracked Revenue</span>
            <strong>$118,421</strong>
          </article>
          <article>
            <span>Edge Health</span>
            <strong>98.2%</strong>
          </article>
          <article>
            <span>Open Reviews</span>
            <strong>6</strong>
          </article>
        </div>
      </header>

      <div className="dashboard-grid">
        <SectionCard title="Affiliate tracking overview" subtitle="Partner performance and first-party attribution." >
          <div className="kpi-row">
            <article><span>Tracked Clicks</span><strong>36,107</strong></article>
            <article><span>Conversions</span><strong>2,006</strong></article>
            <article><span>Conversion Rate</span><strong>5.55%</strong></article>
            <article><span>Net Revenue</span><strong>$118,810</strong></article>
          </div>
          <table>
            <thead>
              <tr><th>Partner</th><th>Clicks</th><th>Conversions</th><th>Revenue</th><th>Status</th></tr>
            </thead>
            <tbody>
              {partnerRows.map((row) => (
                <tr key={row.partner}>
                  <td>{row.partner}</td>
                  <td>{row.clicks.toLocaleString()}</td>
                  <td>{row.conversions}</td>
                  <td>{row.revenue}</td>
                  <td><span className={`pill ${row.status === 'Healthy' ? 'ok' : 'warn'}`}>{row.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </SectionCard>

        <SectionCard title="Approval queue" subtitle="Human-reviewed outbound publishing pipeline." >
          <div className="form-grid">
            <label>
              Campaign
              <input defaultValue="Spring partner launch" />
            </label>
            <label>
              Daily approval cap
              <input defaultValue="18" type="number" />
            </label>
            <label>
              Region
              <select defaultValue="US">
                <option>US</option>
                <option>UK</option>
                <option>CA</option>
              </select>
            </label>
            <label>
              Review lane
              <select defaultValue="Compliance">
                <option>Compliance</option>
                <option>Creative</option>
                <option>Finance</option>
              </select>
            </label>
          </div>
          <ul className="queue-list">
            {approvalQueue.map((job) => (
              <li key={job.owner + job.asset}>
                <div>
                  <p>{job.asset}</p>
                  <small>{job.owner} • {job.slot}</small>
                </div>
                <span className="pill info">{job.state}</span>
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard title="Edge routing map" subtitle="Recommended `*.zeaz.dev` service boundaries." >
          <table>
            <thead>
              <tr><th>Hostname</th><th>Service</th><th>Control</th></tr>
            </thead>
            <tbody>
              {edgeRoutes.map((route) => (
                <tr key={route.host}>
                  <td>{route.host}</td>
                  <td>{route.service}</td>
                  <td>{route.control}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </SectionCard>

        <SectionCard title="Go-live checklist" subtitle="Operational readiness before exposing production traffic." >
          <ul className="checklist">
            {goLiveChecklist.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </SectionCard>
      </div>
    </main>
  )
}
