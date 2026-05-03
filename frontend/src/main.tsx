import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Activity, Archive, Check, Download, FileText, Gauge, LayoutDashboard, Plus, ShieldCheck, Upload, Users } from 'lucide-react'
import React, { useMemo, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import './styles.css'

type Checklist = {
  id: string
  title: string
  description: string
  framework_refs: { framework: string; id: string; name: string }[]
  completed: boolean
  notes: string
}

type Artifact = {
  id: string
  artifact_type: string
  filename: string
  file_size: number
  mime_type: string
  sha256: string
}

type Phase = {
  id: number
  phase_key: string
  name: string
  description: string
  status: 'not_started' | 'in_progress' | 'pending_approval' | 'approved' | 'skipped'
  approver_notes: string
  phase_data: { required_artifacts?: string[] }
  checklist_items: Checklist[]
  artifacts: Artifact[]
}

type Project = {
  id: string
  name: string
  description: string
  system_type: string
  risk_tier: string
  status: string
  current_phase_key: string
  phases: Phase[]
}

type Evidence = {
  id: string
  generated_at: string
  phases_included: string[]
  format: string
  package_hash: string
  status: string
}

const apiBase = import.meta.env.VITE_API_URL ?? '/api/v1'
const navItems = [
  ['dashboard', LayoutDashboard],
  ['projects', Gauge],
  ['evidence', FileText],
  ['frameworks', Archive],
  ['admin', Users]
] as const

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase}${path}`, init)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

function cx(...classes: Array<string | false | undefined>) {
  return classes.filter(Boolean).join(' ')
}

function App() {
  const [route, setRoute] = useState('dashboard')
  const projects = useQuery({ queryKey: ['projects'], queryFn: () => api<Project[]>('/projects') })
  const activeProjectId = projects.data?.[0]?.id

  return (
    <div className="min-h-screen bg-page text-high">
      <aside className="fixed inset-y-0 left-0 w-20 border-r border-border bg-surface">
        <div className="flex h-16 items-center justify-center border-b border-border text-accent"><ShieldCheck /></div>
        <nav className="flex flex-col items-center gap-3 py-4">
          {navItems.map(([name, Icon]) => (
            <button key={name} title={name} onClick={() => setRoute(name)} className={cx('grid h-11 w-11 place-items-center rounded border border-transparent text-low hover:border-border hover:text-high', route === name && 'border-accent text-accent')}>
              <Icon size={19} />
            </button>
          ))}
        </nav>
      </aside>
      <main className="ml-20">
        <header className="flex h-16 items-center justify-between border-b border-border bg-surface px-6">
          <div>
            <h1 className="text-lg font-semibold">AI-SGP</h1>
            <p className="text-xs text-low">AI security governance and examination evidence</p>
          </div>
          <div className="rounded border border-border px-3 py-1 text-sm text-medium">Demo Admin</div>
        </header>
        {route === 'dashboard' && <Dashboard projects={projects.data ?? []} />}
        {route === 'projects' && <Projects projects={projects.data ?? []} />}
        {route === 'evidence' && activeProjectId && <EvidencePage projectId={activeProjectId} />}
        {route === 'frameworks' && <Frameworks />}
        {route === 'admin' && <Admin />}
      </main>
    </div>
  )
}

const queryClient = new QueryClient()

function Dashboard({ projects }: { projects: Project[] }) {
  const data = useMemo(() => [1, 2, 3].map((tier) => ({ name: `Tier ${tier}`, value: projects.filter((p) => p.risk_tier === String(tier)).length })), [projects])
  const pending = projects.flatMap((p) => p.phases ?? []).filter((p) => p.status === 'pending_approval').length
  return (
    <section className="space-y-6 p-6">
      <div className="grid gap-4 md:grid-cols-4">
        <Metric label="Projects" value={projects.length} />
        <Metric label="Pending approval" value={pending} tone="warning" />
        <Metric label="Active systems" value={projects.filter((p) => p.status === 'active').length} />
        <Metric label="Evidence ready" value="MVP" tone="success" />
      </div>
      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <div className="rounded border border-border bg-card p-4">
          <h2 className="mb-3 text-sm font-semibold">Risk Tier Distribution</h2>
          <div className="h-72">
            <ResponsiveContainer>
              <PieChart>
                <Pie dataKey="value" data={data} innerRadius={68} outerRadius={100} paddingAngle={3}>
                  {data.map((_, i) => <Cell key={i} fill={['#38d4f5', '#f5b838', '#f55252'][i]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <ProjectWorkspace projectId={projects[0]?.id} />
      </div>
    </section>
  )
}

function Metric({ label, value, tone = 'accent' }: { label: string; value: React.ReactNode; tone?: 'accent' | 'warning' | 'success' }) {
  return (
    <div className="rounded border border-border bg-card p-4">
      <p className="text-xs uppercase text-low">{label}</p>
      <p className={cx('mt-2 text-3xl font-semibold', tone === 'accent' && 'text-accent', tone === 'warning' && 'text-warning', tone === 'success' && 'text-success')}>{value}</p>
    </div>
  )
}

function Projects({ projects }: { projects: Project[] }) {
  const qc = useQueryClient()
  const create = useMutation({
    mutationFn: () => api<Project>('/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: `AI System ${projects.length + 1}`, description: 'New governed AI system', system_type: 'llm_chatbot', risk_tier: '2' }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] })
  })
  return (
    <section className="space-y-5 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Projects</h2>
        <button onClick={() => create.mutate()} className="inline-flex items-center gap-2 rounded border border-accent px-3 py-2 text-sm text-accent"><Plus size={16} />Create</button>
      </div>
      <div className="overflow-hidden rounded border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-surface text-low"><tr><th className="p-3">Name</th><th>Type</th><th>Risk</th><th>Phase</th><th>Status</th></tr></thead>
          <tbody>{projects.map((p) => <tr key={p.id} className="border-t border-border"><td className="p-3 text-high">{p.name}</td><td>{p.system_type}</td><td>{p.risk_tier}</td><td>{p.current_phase_key}</td><td>{p.status}</td></tr>)}</tbody>
        </table>
      </div>
      <ProjectWorkspace projectId={projects[0]?.id} />
    </section>
  )
}

function ProjectWorkspace({ projectId }: { projectId?: string }) {
  const [phaseKey, setPhaseKey] = useState<string>()
  const project = useQuery({ queryKey: ['project', projectId], queryFn: () => api<Project>(`/projects/${projectId}`), enabled: Boolean(projectId) })
  const phase = project.data?.phases.find((p) => p.phase_key === (phaseKey ?? project.data?.current_phase_key)) ?? project.data?.phases[0]
  if (!projectId || !project.data || !phase) return <div className="rounded border border-border bg-card p-5 text-low">No project selected.</div>
  return (
    <div className="grid min-h-[620px] overflow-hidden rounded border border-border bg-surface lg:grid-cols-[240px_1fr_280px]">
      <div className="border-r border-border p-3">
        {project.data.phases.map((p) => <button key={p.phase_key} onClick={() => setPhaseKey(p.phase_key)} className={cx('mb-2 flex w-full items-center gap-2 rounded border border-border p-2 text-left text-xs', p.phase_key === phase.phase_key && 'border-accent text-accent')}><span className={cx('h-2.5 w-2.5 rounded-full', statusDot(p.status))} />{p.phase_key.replace('_', ' ')}</button>)}
      </div>
      <PhasePanel projectId={projectId} phase={phase} />
      <Coverage phase={phase} />
    </div>
  )
}

function statusDot(status: Phase['status']) {
  return status === 'approved' ? 'bg-success' : status === 'pending_approval' ? 'bg-warning' : status === 'in_progress' ? 'bg-accent' : 'bg-low'
}

function PhasePanel({ projectId, phase }: { projectId: string; phase: Phase }) {
  const qc = useQueryClient()
  const toggle = useMutation({
    mutationFn: (item: Checklist) => api(`/projects/${projectId}/phases/${phase.phase_key}/checklist/${item.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ completed: !item.completed, notes: item.notes }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project', projectId] })
  })
  const submit = useMutation({ mutationFn: () => api(`/projects/${projectId}/phases/${phase.phase_key}/submit`, { method: 'POST' }), onSuccess: () => qc.invalidateQueries({ queryKey: ['project', projectId] }) })
  const approve = useMutation({ mutationFn: (approved: boolean) => api(`/projects/${projectId}/phases/${phase.phase_key}/approve`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ approved, notes: approved ? 'Approved in AI-SGP workspace.' : 'Returned for remediation.' }) }), onSuccess: () => qc.invalidateQueries({ queryKey: ['project', projectId] }) })
  return (
    <div className="space-y-5 p-5">
      <div>
        <p className="text-xs uppercase text-low">{phase.phase_key}</p>
        <h2 className="text-xl font-semibold">{phase.name}</h2>
        <p className="mt-1 text-sm text-medium">{phase.description}</p>
      </div>
      <div className="space-y-2">
        {phase.checklist_items.map((item) => (
          <button key={item.id} onClick={() => toggle.mutate(item)} className="flex w-full gap-3 rounded border border-border bg-card p-3 text-left hover:border-accent">
            <span className={cx('mt-1 grid h-5 w-5 shrink-0 place-items-center rounded border', item.completed ? 'border-success bg-success text-page' : 'border-low')}><Check size={14} /></span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm text-high">{item.title}</span>
              <span className="mt-2 flex flex-wrap gap-1">{item.framework_refs.map((r) => <span key={`${r.framework}${r.id}`} className="rounded border border-border px-2 py-0.5 text-[11px] text-low">{r.framework} {r.id}</span>)}</span>
            </span>
          </button>
        ))}
      </div>
      <ArtifactUpload projectId={projectId} phase={phase} />
      <div className="flex flex-wrap gap-2">
        <button onClick={() => submit.mutate()} className="rounded border border-accent px-3 py-2 text-sm text-accent">Submit for Approval</button>
        <button onClick={() => approve.mutate(true)} className="rounded border border-success px-3 py-2 text-sm text-success">Approve</button>
        <button onClick={() => approve.mutate(false)} className="rounded border border-danger px-3 py-2 text-sm text-danger">Reject</button>
      </div>
    </div>
  )
}

function ArtifactUpload({ projectId, phase }: { projectId: string; phase: Phase }) {
  const qc = useQueryClient()
  const upload = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('artifact_type', phase.phase_data.required_artifacts?.[0] ?? 'other')
      form.append('description', 'Workspace upload')
      form.append('file', file)
      return api(`/projects/${projectId}/phases/${phase.phase_key}/artifacts`, { method: 'POST', body: form })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project', projectId] })
  })
  return (
    <div className="rounded border border-border bg-card p-3">
      <label className="flex cursor-pointer items-center justify-center gap-2 rounded border border-dashed border-border p-4 text-sm text-medium hover:border-accent">
        <Upload size={16} /> Artifact upload
        <input type="file" className="hidden" onChange={(event) => event.target.files?.[0] && upload.mutate(event.target.files[0])} />
      </label>
      <div className="mt-3 space-y-2 text-xs text-low">
        {phase.artifacts.map((artifact) => <div key={artifact.id} className="flex items-center justify-between rounded bg-surface p-2"><span>{artifact.filename}</span><span>{artifact.artifact_type}</span></div>)}
      </div>
    </div>
  )
}

function Coverage({ phase }: { phase: Phase }) {
  const refs = phase.checklist_items.flatMap((item) => item.framework_refs.map((ref) => ({ ...ref, completed: item.completed })))
  return (
    <div className="border-l border-border p-4">
      <h3 className="mb-3 text-sm font-semibold">Framework Coverage</h3>
      <div className="space-y-2">{refs.map((ref, index) => <div key={index} className="flex items-center justify-between rounded border border-border p-2 text-xs"><span>{ref.framework} {ref.id}</span><span className={ref.completed ? 'text-success' : 'text-warning'}>{ref.completed ? 'addressed' : 'gap'}</span></div>)}</div>
    </div>
  )
}

function EvidencePage({ projectId }: { projectId: string }) {
  const qc = useQueryClient()
  const project = useQuery({ queryKey: ['project', projectId], queryFn: () => api<Project>(`/projects/${projectId}`) })
  const evidence = useQuery({ queryKey: ['evidence', projectId], queryFn: () => api<Evidence[]>(`/projects/${projectId}/evidence`) })
  const [format, setFormat] = useState('pdf')
  const generate = useMutation({
    mutationFn: () => api<Evidence>(`/projects/${projectId}/evidence`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phases_included: project.data?.phases.map((p) => p.phase_key) ?? [], format }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['evidence', projectId] })
  })
  return (
    <section className="space-y-5 p-6">
      <h2 className="text-xl font-semibold">Evidence Packages</h2>
      <div className="rounded border border-border bg-card p-4">
        <div className="mb-4 flex gap-2">{['pdf', 'json', 'yaml', 'csv'].map((f) => <button key={f} onClick={() => setFormat(f)} className={cx('rounded border px-3 py-2 text-sm', format === f ? 'border-accent text-accent' : 'border-border text-medium')}>{f.toUpperCase()}</button>)}</div>
        <button onClick={() => generate.mutate()} className="inline-flex items-center gap-2 rounded border border-accent px-3 py-2 text-sm text-accent"><FileText size={16} />Generate</button>
      </div>
      <div className="space-y-2">{evidence.data?.map((pkg) => <a key={pkg.id} href={`${apiBase}/evidence/${pkg.id}/download`} className="flex items-center justify-between rounded border border-border bg-card p-3 text-sm"><span>{pkg.format.toUpperCase()} {pkg.package_hash.slice(0, 12)}</span><Download size={16} /></a>)}</div>
    </section>
  )
}

function Frameworks() {
  const data = useQuery({ queryKey: ['frameworks'], queryFn: () => api<Array<{ id: number; framework: string; reference_id: string; phase_key: string; description: string; severity: string }>>('/frameworks') })
  return <section className="p-6"><h2 className="mb-5 text-xl font-semibold">Frameworks</h2><div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">{data.data?.slice(0, 120).map((row) => <div key={row.id} className="rounded border border-border bg-card p-3 text-sm"><div className="text-accent">{row.framework} {row.reference_id}</div><div className="text-xs text-low">{row.phase_key} | {row.severity}</div><p className="mt-2 text-medium">{row.description}</p></div>)}</div></section>
}

function Admin() {
  const audit = useQuery({ queryKey: ['audit'], queryFn: () => api<Array<{ id: string; action: string; entity_type: string; timestamp: string }>>('/admin/audit-log') })
  return <section className="p-6"><h2 className="mb-5 text-xl font-semibold">Admin</h2><div className="rounded border border-border bg-card"><div className="border-b border-border p-3 text-sm font-semibold">Audit Log</div>{audit.data?.map((row) => <div key={row.id} className="flex items-center gap-3 border-b border-border p-3 text-sm text-medium"><Activity size={15} className="text-accent" />{row.action}<span className="ml-auto text-low">{new Date(row.timestamp).toLocaleString()}</span></div>)}</div></section>
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>
)
