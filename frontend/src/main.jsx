import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, ArrowUpRight, BarChart3, ChevronRight, CircleDollarSign, Sparkles, Users } from 'lucide-react'
import './styles.css'

const customers = [
  { name: 'Ava Mitchell', clv: '$8,420', segment: 'High value', confidence: '84%', monthly_spend: 180, purchase_frequency: 3.2, tenure_months: 14, churn_risk: 18, acquisition_cost: 72 },
  { name: 'Noah Wilson', clv: '$5,180', segment: 'Growth potential', confidence: '72%', monthly_spend: 145, purchase_frequency: 2.6, tenure_months: 9, churn_risk: 28, acquisition_cost: 64 },
  { name: 'Mia Johnson', clv: '$1,940', segment: 'Nurture', confidence: '65%', monthly_spend: 65, purchase_frequency: 1.5, tenure_months: 4, churn_risk: 46, acquisition_cost: 49 },
]
const initial = { customer_name: 'Ava Mitchell', monthly_spend: 180, purchase_frequency: 3.2, tenure_months: 14, churn_risk: 18, acquisition_cost: 72 }

function App() {
  const [form, setForm] = useState(initial)
  const [result, setResult] = useState({ predicted_clv: 8420, confidence: 84, segment: 'High value', retention: 82, monthly_value: 350.83 })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [page, setPage] = useState('Overview')
  const [showAll, setShowAll] = useState(false)
  const [notice, setNotice] = useState('')
  const update = e => setForm({ ...form, [e.target.name]: e.target.value })
  const predict = async e => {
    e.preventDefault(); setLoading(true); setError('')
    try { const r = await fetch('/api/predict/', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(form) }); const data = await r.json(); if (!r.ok) throw Error(data.detail); setResult(data) }
    catch (err) { setError(err.message || 'Could not reach the prediction service.') }
    finally { setLoading(false) }
  }
  const money = n => new Intl.NumberFormat('en-US', {style:'currency', currency:'USD', maximumFractionDigits:0}).format(n)
  const loadCustomer = customer => {
    setForm({ customer_name: customer.name, monthly_spend: customer.monthly_spend, purchase_frequency: customer.purchase_frequency, tenure_months: customer.tenure_months, churn_risk: customer.churn_risk, acquisition_cost: customer.acquisition_cost })
    setNotice(`${customer.name}'s signals loaded into the prediction form.`)
    document.querySelector('.prediction')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
  const exportReport = () => {
    const rows = [['Customer', 'Projected CLV', 'Segment', 'Confidence'], ...customers.map(c => [c.name, c.clv, c.segment, c.confidence])]
    const file = new Blob([rows.map(row => row.join(',')).join('\n')], { type: 'text/csv' })
    const link = document.createElement('a'); link.href = URL.createObjectURL(file); link.download = 'lumen-clv-report.csv'; link.click(); URL.revokeObjectURL(link.href)
    setNotice('Your customer value report has been downloaded.')
  }
  const goTo = pageName => {
    const target = pageName === 'Overview' ? 'overview' : pageName === 'Customers' ? 'customers' : 'predictions'
    setPage(pageName)
    document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  const navItems = [{ label: 'Overview', icon: <BarChart3/> }, { label: 'Customers', icon: <Users/> }, { label: 'Predictions', icon: <Activity/> }]
  return <div className="shell">
    <aside><button className="brand" onClick={() => goTo('Overview')} aria-label="Go to overview"><span>l</span> lumen</button><div className="workspace">WORKSPACE</div><nav>{navItems.map(item => <button key={item.label} className={page === item.label ? 'active' : ''} onClick={() => goTo(item.label)}>{item.icon}{item.label}</button>)}</nav><button className="side-card" onClick={() => goTo('Predictions')}><Sparkles/><strong>Sharper insights</strong><p>Use customer signals to make every relationship count.</p></button><button className="profile" onClick={() => setNotice('Signed in as Leah Morgan, Growth team.')}><div className="avatar">LM</div><div><b>Leah Morgan</b><small>Growth team</small></div><ChevronRight size={16}/></button></aside>
    <main><header id="overview"><div><p className="eyebrow">CUSTOMER INTELLIGENCE · {page.toUpperCase()}</p><h1>Understand tomorrow’s value,<br/><i>today.</i></h1><p className="intro">Predict customer lifetime value and make confident decisions with your highest-impact relationships.</p></div><button className="export" onClick={exportReport}>Export report <ArrowUpRight size={16}/></button></header>
      {notice && <div className="notice" role="status">{notice}<button onClick={() => setNotice('')} aria-label="Dismiss notification">×</button></div>}
      <section className="metrics"><Metric icon={<CircleDollarSign/>} title="Portfolio value" value="$482,750" note="12.4% from last month" onClick={() => setNotice('Portfolio value includes the projected value of all active customers.')}/><Metric icon={<Users/>} title="Active customers" value="1,248" note="8.1% from last month" onClick={() => { setPage('Customers'); setShowAll(true) }}/><Metric icon={<Activity/>} title="Average CLV" value="$3,682" note="4.6% from last month" onClick={() => { setPage('Predictions'); document.querySelector('.prediction')?.scrollIntoView({ behavior: 'smooth' }) }}/></section>
      <section className="work" id="predictions"><div className="panel prediction"><div className="panel-head"><div><p className="eyebrow">CLV FORECAST</p><h2>Customer value prediction</h2></div><span className="live"><b/> Live model</span></div><form onSubmit={predict}><div className="name-input"><label>Customer name</label><input name="customer_name" value={form.customer_name} onChange={update}/></div><div className="fields"><Field label="Monthly spend" name="monthly_spend" prefix="$" form={form} update={update}/><Field label="Purchases / month" name="purchase_frequency" form={form} update={update}/><Field label="Tenure" name="tenure_months" suffix="months" form={form} update={update}/><Field label="Churn risk" name="churn_risk" suffix="%" form={form} update={update}/><Field label="Acquisition cost" name="acquisition_cost" prefix="$" form={form} update={update}/></div><button className="predict" disabled={loading}>{loading ? 'Analyzing signals…' : <>Generate prediction <ArrowUpRight size={17}/></>}</button>{error && <p className="error">{error}</p>}</form></div>
      <div className="result"><p className="eyebrow">PROJECTED LIFETIME VALUE</p><div className="value">{money(result.predicted_clv)}</div><div className="confidence"><span>{result.confidence}%</span><div><b>Prediction confidence</b><div className="progress"><i style={{width:result.confidence+'%'}}/></div></div></div><div className="segment"><span>Customer segment</span><b>{result.segment}</b></div><p className="recommend"><Sparkles size={16}/> Prioritize retention — estimated {result.retention}% retention likelihood.</p></div></section>
      <section className="customer-panel" id="customers"><div className="table-title"><div><p className="eyebrow">RECENTLY ANALYZED</p><h2>Customer signals</h2></div><button onClick={() => setShowAll(!showAll)}>{showAll ? 'Show recent' : 'View all customers'} <ChevronRight size={16}/></button></div><div className="table">{customers.slice(0, showAll ? customers.length : 2).map((c,i)=><button className="row" key={c.name} onClick={() => loadCustomer(c)} aria-label={`Load ${c.name} into prediction form`}><div className="customer"><div className={'avatar a'+i}>{c.name.split(' ').map(x=>x[0]).join('')}</div><b>{c.name}</b></div><b>{c.clv}</b><span className={'tag t'+i}>{c.segment}</span><span>{c.confidence} confidence</span><ChevronRight size={17}/></button>)}</div></section>
    </main></div>
}
function Field({label,name,prefix,suffix,form,update}) { return <label className="field">{label}<span className="field-wrap">{prefix&&<em>{prefix}</em>}<input type="number" step="any" name={name} value={form[name]} onChange={update}/>{suffix&&<em>{suffix}</em>}</span></label> }
function Metric({icon,title,value,note,onClick}) { return <button className="metric" onClick={onClick}><span className="metric-icon">{icon}</span><div><p>{title}</p><h3>{value}</h3><small>↗ {note}</small></div></button> }
createRoot(document.getElementById('root')).render(<App />)
