import SectionCard from '../components/SectionCard'

const affiliateRows = [
  { partner: 'CreatorHub', clicks: 14222, conversions: 812, revenue: '$48,720', status: 'Healthy' },
  { partner: 'TrendNova', clicks: 9831, conversions: 461, revenue: '$28,110', status: 'Needs Review' },
  { partner: 'ShopPulse', clicks: 12054, conversions: 733, revenue: '$41,980', status: 'Healthy' }
]

const automationQueue = [
  { account: '@zttato_official', video: 'Top 5 gadgets under $30', slot: '13:00 UTC', state: 'Scheduled' },
  { account: '@zttato_reviews', video: 'UGC ad variant B', slot: '14:30 UTC', state: 'Rendering' },
  { account: '@zttato_deals', video: 'Flash sale countdown', slot: '16:00 UTC', state: 'Awaiting Approval' }
]

const productIdeas = [
  { keyword: 'portable blender', score: 92, demand: 'High', margin: '37%' },
  { keyword: 'desk walking pad', score: 87, demand: 'High', margin: '29%' },
  { keyword: 'wireless car vacuum', score: 83, demand: 'Medium', margin: '34%' }
]

export default function HomePage() {
  return (
    <main className="dashboard-root">
      <header className="hero">
        <div>
          <p className="badge">Production</p>
          <h1>ZTTATO Admin Dashboard</h1>
          <p>Unified operations for affiliate tracking, TikTok video automation, and AI-powered product discovery.</p>
        </div>
        <div className="hero-stats">
          <article>
            <span>Total GMV</span>
            <strong>$118,421</strong>
          </article>
          <article>
            <span>Automation Health</span>
            <strong>98.2%</strong>
          </article>
          <article>
            <span>New Product Leads</span>
            <strong>54</strong>
          </article>
        </div>
      </header>

      <div className="dashboard-grid">
        <SectionCard title="Real Affiliate Tracking UI" subtitle="Live campaign and partner conversion observability.">
          <div className="kpi-row">
            <article><span>Tracked Clicks</span><strong>36,107</strong></article>
            <article><span>Conversions</span><strong>2,006</strong></article>
            <article><span>Conversion Rate</span><strong>5.55%</strong></article>
            <article><span>Net Revenue</span><strong>$118,810</strong></article>
          </div>
          <table>
            <thead>
              <tr><th>Affiliate</th><th>Clicks</th><th>Conversions</th><th>Revenue</th><th>Status</th></tr>
            </thead>
            <tbody>
              {affiliateRows.map((row) => (
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

        <SectionCard title="TikTok Video Automation UI" subtitle="Pipeline for generation, approvals, and scheduled posting.">
          <div className="form-grid">
            <label>
              Campaign
              <input defaultValue="Spring Viral Boost" />
            </label>
            <label>
              Daily Upload Cap
              <input defaultValue="18" type="number" />
            </label>
            <label>
              Target Region
              <select defaultValue="US">
                <option>US</option>
                <option>UK</option>
                <option>CA</option>
              </select>
            </label>
            <label>
              AI Caption Style
              <select defaultValue="Story Hook">
                <option>Story Hook</option>
                <option>Problem/Solution</option>
                <option>Authority Proof</option>
              </select>
            </label>
          </div>
          <ul className="queue-list">
            {automationQueue.map((job) => (
              <li key={job.account + job.video}>
                <div>
                  <p>{job.video}</p>
                  <small>{job.account} • {job.slot}</small>
                </div>
                <span className="pill info">{job.state}</span>
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard title="AI Product Finder UI" subtitle="Trend scoring based on demand, margin, and competition signals.">
          <div className="finder-toolbar">
            <input placeholder="Search keyword, niche, or product type" defaultValue="smart home" />
            <button type="button">Run AI Scan</button>
          </div>
          <table>
            <thead>
              <tr><th>Keyword</th><th>Opportunity Score</th><th>Demand</th><th>Est. Margin</th></tr>
            </thead>
            <tbody>
              {productIdeas.map((idea) => (
                <tr key={idea.keyword}>
                  <td>{idea.keyword}</td>
                  <td>{idea.score}</td>
                  <td>{idea.demand}</td>
                  <td>{idea.margin}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </SectionCard>
      </div>
    </main>
  )
}
