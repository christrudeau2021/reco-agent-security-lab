import { useEffect, useState } from 'react'
import './App.css'
import { fetchAgents, fetchViolations } from './lib/aim'
import { fetchGitHubInventory, fetchIdentityInventory, fetchToxicOAuthGrants } from './lib/neo4j'
import { Discover } from './tabs/Discover'
import { Prioritize } from './tabs/Prioritize'
import { Remediate } from './tabs/Remediate'
import type { LabData } from './types'

type Tab = 'discover' | 'prioritize' | 'remediate'

function App() {
  const [tab, setTab] = useState<Tab>('discover')
  const [data, setData] = useState<LabData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [identity, github, agents, violations, toxicGrants] = await Promise.all([
          fetchIdentityInventory(),
          fetchGitHubInventory(),
          fetchAgents(),
          fetchViolations(),
          fetchToxicOAuthGrants(),
        ])
        if (!cancelled) {
          setData({ identity, github, agents, violations, toxicGrants })
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <h1>Ecosystem Security Lab</h1>
        <p className="app-subtitle">
          Independent, open-source demo lab for AI agent &amp; SaaS identity
          security — not affiliated with or endorsed by any commercial
          vendor.
        </p>
      </header>

      <nav className="tab-nav">
        <button className={tab === 'discover' ? 'active' : ''} onClick={() => setTab('discover')}>
          Discover
        </button>
        <button className={tab === 'prioritize' ? 'active' : ''} onClick={() => setTab('prioritize')}>
          Prioritize
        </button>
        <button className={tab === 'remediate' ? 'active' : ''} onClick={() => setTab('remediate')}>
          Remediate
        </button>
      </nav>

      <main>
        {error && <p className="error-banner">Failed to load: {error}</p>}
        {!data && !error && <p className="loading">Loading…</p>}
        {data && tab === 'discover' && <Discover data={data} />}
        {data && tab === 'prioritize' && <Prioritize data={data} />}
        {data && tab === 'remediate' && <Remediate data={data} />}
      </main>
    </div>
  )
}

export default App
