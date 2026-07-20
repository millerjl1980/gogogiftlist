import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type Giver = { id: number; name: string; email: string }
type Gift = { id: number; name: string; detail: string; url?: string; giverId?: number }
type GiftList = { id: number; receiver: string; occasion: string; date: string; gifts: Gift[] }

const API_URL = 'http://localhost:8000/api'
let csrfToken = ''

async function api(path: string, method = 'GET', data?: object) {
  const response = await fetch(`${API_URL}${path}`, {
    method,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}) },
    ...(data ? { body: JSON.stringify(data) } : {}),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || 'Something went wrong. Please try again.')
  return body
}

function App() {
  const [signedIn, setSignedIn] = useState(false)
  const [signUp, setSignUp] = useState(true)
  const [view, setView] = useState<'lists' | 'givers' | 'portal'>('lists')
  const [lists, setLists] = useState<GiftList[]>([])
  const [givers, setGivers] = useState<Giver[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [selectedGiverId, setSelectedGiverId] = useState<number | null>(null)
  const [portalGifts, setPortalGifts] = useState<Array<Gift & { receiver: string; occasion: string }>>([])
  const [modal, setModal] = useState<'list' | 'gift' | 'giver' | null>(null)
  const [notice, setNotice] = useState('')
  const active = lists.find((list) => list.id === activeId) ?? lists[0]
  const giver = givers.find((item) => item.id === selectedGiverId) ?? givers[0]
  const assigned = useMemo(() => active && giver ? active.gifts.filter((gift) => gift.giverId === giver.id) : [], [active, giver])
  const giftText = active ? `${active.receiver}'s ${active.occasion} gift list\n\n${assigned.map((gift, index) => `${index + 1}. ${gift.name}${gift.detail ? ` — ${gift.detail}` : ''}${gift.url ? `\n   ${gift.url}` : ''}`).join('\n') || 'No gifts have been assigned yet.'}\n\nThanks for helping make this special!` : ''

  const loadWorkspace = async () => {
    const [listResponse, giverResponse] = await Promise.all([api('/lists/'), api('/givers/')])
    const loadedLists = listResponse.lists.map((list: { id: number; receiver: string; occasion: string; date: string; gifts: Array<{ id: number; name: string; detail: string; url: string; giver_id: number | null }> }) => ({ ...list, gifts: list.gifts.map((gift) => ({ ...gift, giverId: gift.giver_id, url: gift.url || undefined })) }))
    setLists(loadedLists)
    setGivers(giverResponse.givers)
    setActiveId((current) => current ?? loadedLists[0]?.id ?? null)
    setSelectedGiverId((current) => current ?? giverResponse.givers[0]?.id ?? null)
  }

  useEffect(() => {
    fetch(`${API_URL}/csrf/`, { credentials: 'include' }).then((response) => response.json()).then((data) => { csrfToken = data.csrfToken; return api('/me/') }).then(() => { setSignedIn(true); return loadWorkspace() }).catch(() => undefined)
  }, [])

  const addList = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const data = new FormData(event.currentTarget); const receiver = String(data.get('receiver')).trim(); const occasion = String(data.get('occasion')).trim()
    if (!receiver || !occasion) return
    try {
      const response = await api('/lists/', 'POST', { receiver, occasion, date: data.get('date') })
      const list = { ...response.list, gifts: [] }
      setLists((items) => [list, ...items]); setActiveId(list.id); setModal(null); setNotice(`${receiver}'s list is ready for gifts.`)
    } catch (error) { setNotice(error instanceof Error ? error.message : 'Unable to create list.') }
  }
  const addGift = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const data = new FormData(event.currentTarget); const name = String(data.get('name')).trim(); const detail = String(data.get('detail')).trim(); const url = String(data.get('url')).trim()
    if (!name && !detail && !url) return
    if (!active) return
    try {
      const response = await api(`/lists/${active.id}/gifts/`, 'POST', { name, detail, url })
      const gift = { ...response.gift, giverId: response.gift.giver_id, url: response.gift.url || undefined }
      setLists((items) => items.map((list) => list.id === active.id ? { ...list, gifts: [...list.gifts, gift] } : list)); setModal(null)
    } catch (error) { setNotice(error instanceof Error ? error.message : 'Unable to add gift.') }
  }
  const addGiver = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const data = new FormData(event.currentTarget); const name = String(data.get('name')).trim(); const email = String(data.get('email')).trim()
    if (!name || !email) return
    try {
      const response = await api('/givers/', 'POST', { name, email })
      const newGiver = response.giver; setGivers((items) => [...items, newGiver]); setSelectedGiverId(newGiver.id); setModal(null)
    } catch (error) { setNotice(error instanceof Error ? error.message : 'Unable to add gift giver.') }
  }
  const assign = async (giftId: number, giverId: string) => {
    try {
      await api(`/gifts/${giftId}/assignment/`, 'POST', { giver_id: giverId ? Number(giverId) : null })
      setLists((items) => items.map((list) => list.id === active?.id ? { ...list, gifts: list.gifts.map((gift) => gift.id === giftId ? { ...gift, giverId: giverId ? Number(giverId) : undefined } : gift) } : list))
    } catch (error) { setNotice(error instanceof Error ? error.message : 'Unable to assign gift.') }
  }
  const copyText = () => { navigator.clipboard?.writeText(giftText); setNotice('Gift list copied to your clipboard.') }

  const authenticateUser = async (name: string, email: string, password: string) => {
    try {
      await api(signUp ? '/auth/register/' : '/auth/login/', 'POST', signUp ? { username: name, email, password } : { email, password })
      setSignedIn(true); await loadWorkspace()
    } catch (error) { setNotice(error instanceof Error ? error.message : 'Unable to sign in.') }
  }
  const openPortal = async () => { setView('portal'); try { const response = await api('/giver/assignments/'); setPortalGifts(response.assignments) } catch (error) { setNotice(error instanceof Error ? error.message : 'Unable to load giver assignments.') } }
  if (!signedIn) return <Auth signUp={signUp} setSignUp={setSignUp} onSubmit={authenticateUser} notice={notice} />
  return <main className="app-shell"><aside className="sidebar"><button className="brand" onClick={() => setView('lists')}><b>G</b> GoGo<span>GiftList</span></button><div className="workspace"><i>JM</i><div><strong>My workspace</strong><small>Signed in</small></div></div><nav><button className={view === 'lists' ? 'active' : ''} onClick={() => setView('lists')}>⌂ <span>My gift lists</span></button><button className={view === 'givers' ? 'active' : ''} onClick={() => setView('givers')}>♧ <span>Gift givers</span></button><button className={view === 'portal' ? 'active' : ''} onClick={openPortal}>▣ <span>Giver portal</span></button></nav><div className="sidebar-bottom"><button>⚙ Settings</button><button onClick={async () => { await api('/auth/logout/', 'POST'); setSignedIn(false); setLists([]) }}>↪ Sign out</button></div></aside><section className="content">{notice && <div className="toast">✓ {notice}<button onClick={() => setNotice('')}>×</button></div>}{view === 'lists' && active && giver && <Lists lists={lists} active={active} givers={givers} giver={giver} selectedGiverId={selectedGiverId ?? 0} text={giftText} setActive={setActiveId} setGiver={setSelectedGiverId} onCreate={() => setModal('list')} onGift={() => setModal('gift')} onAssign={assign} onCopy={copyText} />}{view === 'lists' && !active && <section className="empty"><h2>Your first list starts here.</h2><button className="primary" onClick={() => setModal('list')}>Create a gift list</button></section>}{view === 'givers' && <Givers givers={givers} lists={lists} onNew={() => setModal('giver')} onChoose={(id) => { setSelectedGiverId(id); setView('lists') }} />}{view === 'portal' && <Portal gifts={portalGifts} />}</section>{modal === 'list' && <Modal title="Create a new gift list" close={() => setModal(null)}><form className="form" onSubmit={addList}><Label label="Gift receiver" name="receiver" placeholder="e.g. Maya" required /><Label label="Occasion" name="occasion" placeholder="e.g. Birthday" required /><Label label="Celebration date" name="date" type="date" /><button className="primary">Create gift list</button></form></Modal>}{modal === 'gift' && <Modal title="Add a gift" close={() => setModal(null)}><form className="form" onSubmit={addGift}><p className="hint">Add a link, a note, or both.</p><Label label="Gift name" name="name" placeholder="e.g. Roller skates" /><Label label="Link (optional)" name="url" type="url" placeholder="https://" /><Label label="Details" name="detail" placeholder="Size, color, or a quick note" /><button className="primary">Add gift</button></form></Modal>}{modal === 'giver' && <Modal title="Add a gift giver" close={() => setModal(null)}><form className="form" onSubmit={addGiver}><Label label="Name" name="name" required /><Label label="Email" name="email" type="email" required /><button className="primary">Add gift giver</button></form></Modal>}</main>
}

function Auth({ signUp, setSignUp, onSubmit, notice }: { signUp: boolean; setSignUp: (value: boolean) => void; onSubmit: (name: string, email: string, password: string) => void; notice: string }) { return <main className="auth"><section className="auth-copy"><div className="auth-brand"><b>G</b> GoGo<span>GiftList</span></div><p className="eyebrow">Give better, together</p><h1>Thoughtful gifts.<br /><em>Zero guesswork.</em></h1><p>Bring the people who love someone together around a gift list that feels personal, organized, and joyful.</p><blockquote>“Finally, a way to make group gifting feel easy.”<small>— A very relieved gift planner</small></blockquote></section><section className="auth-form"><div><p className="eyebrow">Welcome to GoGoGiftList</p><h2>{signUp ? 'Create your account' : 'Welcome back'}</h2><p className="muted">{signUp ? 'Start your first shared gift list in a few moments.' : 'Sign in to your gift lists.'}</p>{notice && <p className="auth-error">{notice}</p>}<form className="form" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); onSubmit(String(data.get('name') || ''), String(data.get('email') || ''), String(data.get('password') || '')) }}>{signUp && <Label label="Your name" name="name" placeholder="Jamie Miller" required />}<Label label="Email address" name="email" type="email" placeholder="you@example.com" required /><Label label="Password" name="password" type="password" placeholder="••••••••" required /><button className="primary">{signUp ? 'Create account' : 'Sign in'} <span>→</span></button></form><p className="switch">{signUp ? 'Already have an account?' : 'New to GoGoGiftList?'} <button onClick={() => setSignUp(!signUp)}>{signUp ? 'Sign in' : 'Create one'}</button></p></div></section></main> }

function Lists({ lists, active, givers, giver, selectedGiverId, text, setActive, setGiver, onCreate, onGift, onAssign, onCopy }: { lists: GiftList[]; active: GiftList; givers: Giver[]; giver: Giver; selectedGiverId: number; text: string; setActive: (id: number) => void; setGiver: (id: number) => void; onCreate: () => void; onGift: () => void; onAssign: (gift: number, giver: string) => void; onCopy: () => void }) { const assigned = active.gifts.filter((gift) => gift.giverId).length; return <><header className="page-header"><div><p className="eyebrow">Your lists</p><h1>Make their day <em>beautiful.</em></h1><p className="muted">Create a list, share the joy, and let everyone know exactly how they can help.</p></div><button className="primary" onClick={onCreate}>＋ New gift list</button></header><div className="tabs">{lists.map((list) => <button key={list.id} className={list.id === active.id ? 'active' : ''} onClick={() => setActive(list.id)}><i>{list.receiver[0]}</i><span><strong>{list.receiver}</strong><small>{list.occasion}</small></span></button>)}</div><div className="list-layout"><section><div className="list-heading"><div><p className="eyebrow">{active.date}</p><h2>{active.receiver}'s {active.occasion}</h2><p className="muted">{assigned} of {active.gifts.length} gifts assigned</p></div><div className="progress"><span style={{ width: `${active.gifts.length ? assigned / active.gifts.length * 100 : 0}%` }} /></div></div><div className="gift-table"><div className="table-head"><span>Gift ideas</span><span>Assigned to</span></div>{active.gifts.length === 0 && <p className="empty">No gifts yet. Add an idea to get this list started.</p>}{active.gifts.map((gift) => <div className="gift" key={gift.id}><div><i>{gift.url ? '↗' : '✦'}</i><span><strong>{gift.name}</strong><small>{gift.detail}</small>{gift.url && <a href={gift.url}>View link ↗</a>}</span></div><select value={gift.giverId ?? ''} onChange={(event) => onAssign(gift.id, event.target.value)}><option value="">Unassigned</option>{givers.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></div>)}</div><button className="add" onClick={onGift}>＋ Add a gift idea</button></section><aside className="share"><div className="share-title"><i>{giver.name[0]}</i><div><p className="eyebrow">Gift giver's list</p><h3>{giver.name}</h3></div></div><select value={selectedGiverId} onChange={(event) => setGiver(Number(event.target.value))}>{givers.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><pre>{text}</pre><button className="primary full" onClick={onCopy}>Copy text list</button><a href={`mailto:${giver.email}?subject=${encodeURIComponent(`${active.receiver}'s gift list`)}&body=${encodeURIComponent(text)}`}>✉ Email this list</a><p>You can also invite {giver.name.split(' ')[0]} to sign in and see their assigned gifts.</p></aside></div></> }

function Givers({ givers, lists, onNew, onChoose }: { givers: Giver[]; lists: GiftList[]; onNew: () => void; onChoose: (id: number) => void }) { return <><header className="page-header"><div><p className="eyebrow">Your people</p><h1>Gift givers</h1><p className="muted">The people you can invite to make every list happen.</p></div><button className="primary" onClick={onNew}>＋ Add a giver</button></header><div className="giver-grid">{givers.map((giver) => { const count = lists.flatMap((list) => list.gifts).filter((gift) => gift.giverId === giver.id).length; return <article key={giver.id}><i>{giver.name.split(' ').map((part) => part[0]).join('')}</i><h2>{giver.name}</h2><p>{giver.email}</p><div><b>{count}</b> assigned {count === 1 ? 'gift' : 'gifts'}</div><button onClick={() => onChoose(giver.id)}>View their list →</button></article> })}</div></> }

function Portal({ gifts }: { gifts: Array<Gift & { receiver: string; occasion: string }> }) { return <><header className="page-header"><div><p className="eyebrow">Shared view</p><h1>Giver portal</h1><p className="muted">These are the gifts currently assigned to your giver account.</p></div></header><section className="portal"><div className="portal-head"><i>✓</i><div><p className="eyebrow">Your assignments</p><h2>Ready to give</h2></div></div>{gifts.length === 0 && <p>No gifts are assigned to this account yet.</p>}{gifts.map((gift) => <div className="portal-gift" key={gift.id}><i>✦</i><span><strong>{gift.name}</strong><small>For {gift.receiver}'s {gift.occasion} · {gift.detail}</small></span><button>Mark purchased</button></div>)}</section></> }

function Label({ label, name, type = 'text', placeholder, required }: { label: string; name?: string; type?: string; placeholder?: string; required?: boolean }) { return <label>{label}<input name={name} type={type} placeholder={placeholder} required={required} autoFocus={label === 'Gift receiver' || label === 'Your name' || label === 'Name'} /></label> }
function Modal({ title, close, children }: { title: string; close: () => void; children: React.ReactNode }) { return <div className="backdrop"><section className="modal"><button className="close" onClick={close}>×</button><h2>{title}</h2>{children}</section></div> }
export default App
