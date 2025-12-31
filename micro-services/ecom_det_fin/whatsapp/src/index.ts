import express, { Request, Response, NextFunction } from 'express'
import dotenv from 'dotenv'
import axios from 'axios'
import path from 'node:path'
import fs from 'node:fs'
import * as wppconnect from '@wppconnect-team/wppconnect'

dotenv.config()

const PORT = parseInt(process.env.PORT || '8088', 10)
const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL || 'http://127.0.0.1:8000'
const SESSION = process.env.WHATSAPP_SESSION || 'FactState-Session'
const API_TOKEN = process.env.WHATSAPP_API_TOKEN || ''
const CHROME_PATH = process.env.CHROME_PATH || ''
const DEFAULT_PHONE = process.env.DEFAULT_PHONE || ''
const HEADLESS = (process.env.HEADLESS || 'true').toLowerCase() !== 'false'
const AUTO_CLOSE = Number.parseInt(process.env.AUTO_CLOSE || '0', 10)
const AUTO_REPLY = (process.env.AUTO_REPLY || 'true').toLowerCase() !== 'false'
const ALLOWED_INBOUND_NUMBERS = (process.env.ALLOWED_INBOUND_NUMBERS || '')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean)

const app = express()
app.use(express.json({ limit: '1mb' }))

async function scanUrl(url: string) {
  const base = (FASTAPI_BASE_URL || '').replace(/\/$/, '')
  const targets = [`${base}/ecommerce/analyze-advanced`, `${base}/api/check-site`]

  let lastErr: any = null
  for (const endpoint of targets) {
    try {
      const { data } = await axios.post(endpoint, { url })
      return data
    } catch (e: any) {
      const status = e?.response?.status
      // If it's not found, try the next known endpoint.
      if (status === 404) {
        lastErr = e
        continue
      }
      throw e
    }
  }
  throw lastErr || new Error('No scan endpoint matched')
}

function formatScanReply(data: any, urlFallback: string) {
  const url = data?.url || urlFallback
  const lines: string[] = []
  lines.push(`Trustify report for: ${url}`)
  if (typeof data?.risk_score === 'number') {
    lines.push(`Badge: ${data.badge} | Risk: ${data.risk_score.toFixed(2)}/100`)
  } else {
    lines.push(`Badge: ${data?.badge || 'Unknown'}`)
  }
  if (data?.scanned_at) {
    lines.push(`Scanned at: ${String(data.scanned_at).replace('T', ' ').replace('Z', '')}`)
  }
  if (Array.isArray(data?.reasons) && data.reasons.length) {
    lines.push('Top reasons:')
    data.reasons.slice(0, 4).forEach((r: any) => {
      lines.push(`- [${r.layer}] ${r.message}`)
    })
  }
  return lines.join('\n')
}

function authMiddleware(req: Request, res: Response, next: NextFunction) {
  if (!API_TOKEN) return next()
  const h = req.headers['x-api-token']
  if (h !== API_TOKEN) return res.status(401).json({ error: 'Unauthorized' })
  next()
}

let clientPromise: Promise<wppconnect.Whatsapp> | null = null
let lastStatus: string | null = null
let lastQrData: string | null = null
let lastInitError: string | null = null
let inboundHandlerRegistered = false
const seenInboundMessageKeys = new Set<string>()
const chatStates = new Map<string, { step: 'await_choice' | 'await_ecom_url' | 'await_image' | 'await_news_query'; updatedAt: number }>()

function normalizeDigits(value: string) {
  return (value || '').replace(/\D/g, '')
}

function wantsMenu(text: string) {
  const t = (text || '').trim().toLowerCase()
  return t === '' || t === 'menu' || t === 'start' || t === 'hi' || t === 'hello' || t === 'hey'
}

function wantsExit(text: string) {
  const t = (text || '').trim().toLowerCase()
  return t === '0' || t === '4' || t === 'exit' || t === 'quit' || t === 'stop' || t === 'end'
}

function greetingText() {
  return [
    'Hi! I am Trustify Bot.',
    'I can help you scan e-commerce sites, verify news, and analyze images.',
    "Type 'menu' anytime to see options, or 'exit' to end."
  ].join('\n')
}

function menuText() {
  return [
    'Choose an option:',
    '1) Ecommerce (scan a website)',
    '2) Image (AI vs Human image check)',
    '3) News (verify a news claim)',
    '4) Exit',
    '',
    'Reply with 1, 2, 3 or 4.'
  ].join('\n')
}

async function sendMenu(client: wppconnect.Whatsapp, chatId: string) {
  const anyClient = client as any
  if (typeof anyClient.sendListMessage === 'function') {
    await anyClient.sendListMessage(chatId, {
      buttonText: 'Select option',
      description: 'Choose what you want to do',
      title: 'Trustify Menu',
      footer: "Reply 'menu' anytime. Reply 'exit' to end.",
      sections: [
        {
          title: 'Services',
          rows: [
            { rowId: 'ecommerce', title: 'Ecommerce', description: 'Scan a website for risk' },
            { rowId: 'image', title: 'Image', description: 'AI vs Human image check' },
            { rowId: 'news', title: 'News', description: 'Verify a news claim' },
            { rowId: 'exit', title: 'Exit', description: 'End this conversation' }
          ]
        }
      ]
    })
    return
  }

  await client.sendText(chatId, menuText())
}

function setChatState(chatId: string, step: 'await_choice' | 'await_ecom_url' | 'await_image' | 'await_news_query') {
  chatStates.set(chatId, { step, updatedAt: Date.now() })
}

function getChatState(chatId: string) {
  return chatStates.get(chatId)
}

function normalizeUrlInput(text: string) {
  const raw = (text || '').trim()
  const httpMatch = raw.match(/https?:\/\/\S+/i)
  if (httpMatch) return httpMatch[0]

  // Accept a plain domain like "amazon.in" and treat it as https.
  const maybeDomain = raw.match(/^[a-z0-9.-]+\.[a-z]{2,}(\/\S*)?$/i)
  if (maybeDomain) return `https://${raw}`

  return null
}

async function fetchNewsVerification(query: string) {
  const base = (FASTAPI_BASE_URL || '').replace(/\/$/, '')
  const { data } = await axios.post(`${base}/news/verify`, { query })
  return data
}

function formatNewsReply(payload: any) {
  const r = payload?.result
  const verdict = r?.parsed_output?.verdict_overall || r?.verdict || 'Uncertain'
  const explanation = (r?.parsed_output?.explanation || r?.explanation || '').toString().trim()
  const lines: string[] = []
  lines.push(`News verdict: ${verdict}`)
  if (explanation) lines.push(explanation.slice(0, 900))
  return lines.join('\n\n')
}

function parseDataUrlOrBase64(input: string, fallbackMime: string) {
  const s = (input || '').trim()
  const m = s.match(/^data:([^;]+);base64,(.+)$/)
  if (m) {
    const mime = m[1] || fallbackMime
    const b64 = m[2]
    return { mime, buffer: Buffer.from(b64, 'base64') }
  }
  // Assume it's raw base64
  return { mime: fallbackMime, buffer: Buffer.from(s, 'base64') }
}

async function analyzeImageFromMessage(client: wppconnect.Whatsapp, msg: any) {
  const anyClient = client as any
  if (typeof anyClient.downloadMedia !== 'function') {
    throw new Error('Media download is not supported by this client build')
  }
  const mime = String(msg?.mimetype || 'image/jpeg')
  const media = await anyClient.downloadMedia(msg)
  const mediaStr = typeof media === 'string' ? media : (media?.data || media?.base64 || '')
  if (!mediaStr) throw new Error('Failed to read image data')

  const { mime: resolvedMime, buffer } = parseDataUrlOrBase64(mediaStr, mime)

  const base = (FASTAPI_BASE_URL || '').replace(/\/$/, '')
  const url = `${base}/image/analyze`

  const FormDataCtor = (global as any).FormData
  const BlobCtor = (global as any).Blob
  const fetchFn = (global as any).fetch
  if (!FormDataCtor || !BlobCtor || typeof fetchFn !== 'function') {
    throw new Error('Node fetch/FormData/Blob is not available in this runtime')
  }

  const fd = new FormDataCtor()
  const filename = resolvedMime.includes('png') ? 'image.png' : 'image.jpg'
  fd.append('file', new BlobCtor([buffer], { type: resolvedMime }), filename)

  const resp = await fetchFn(url, { method: 'POST', body: fd })
  const text = await resp.text()
  if (!resp.ok) {
    throw new Error(text || `Image analyze failed (${resp.status})`)
  }
  try {
    return JSON.parse(text)
  } catch {
    return { raw: text }
  }
}

function formatImageReply(payload: any) {
  const ai = Number(payload?.prediction?.ai)
  const human = Number(payload?.prediction?.human)
  if (!Number.isFinite(ai) || !Number.isFinite(human)) {
    return 'Image analyzed, but could not parse confidence scores.'
  }
  const aiPct = (ai * 100).toFixed(1)
  const humanPct = (human * 100).toFixed(1)
  return [
    'Image result (not 100% reliable):',
    `AI: ${aiPct}%`,
    `Human: ${humanPct}%`
  ].join('\n')
}

function isAllowedSender(senderJid: string) {
  if (ALLOWED_INBOUND_NUMBERS.length === 0) return true
  const senderDigits = normalizeDigits(senderJid)
  const senderLast10 = senderDigits.slice(-10)

  return ALLOWED_INBOUND_NUMBERS.some((raw) => {
    const allowedDigits = normalizeDigits(raw)
    if (!allowedDigits) return false
    if (senderDigits === allowedDigits) return true
    if (allowedDigits.length >= 10 && senderLast10 && allowedDigits.slice(-10) === senderLast10) return true
    return false
  })
}

function rememberInboundKey(key: string) {
  if (!key) return false
  if (seenInboundMessageKeys.has(key)) return true
  seenInboundMessageKeys.add(key)
  // Simple bound to avoid unbounded growth
  if (seenInboundMessageKeys.size > 500) {
    const it = seenInboundMessageKeys.values()
    for (let i = 0; i < 250; i++) {
      const v = it.next().value
      if (!v) break
      seenInboundMessageKeys.delete(v)
    }
  }
  return false
}

function registerInboundHandlers(client: wppconnect.Whatsapp) {
  if (inboundHandlerRegistered) return
  inboundHandlerRegistered = true

  const anyClient = client as any
  if (typeof anyClient.onMessage !== 'function') {
    console.warn('WPPConnect client has no onMessage handler; auto-reply disabled')
    return
  }

  anyClient.onMessage(async (msg: any) => {
    try {
      if (!AUTO_REPLY) return
      if (!msg) return
      if (msg.fromMe) return
      if (msg.isGroupMsg) return

      const chatId = String(msg.from || '')
      if (!chatId) return
      if (!isAllowedSender(chatId)) return

      const messageText = String(msg.body || '').trim()
      // Allow empty messageText for media.

      const key = msg.id ? (typeof msg.id === 'string' ? msg.id : JSON.stringify(msg.id)) : `${chatId}:${msg.t || ''}:${messageText.slice(0, 40)}`
      if (rememberInboundKey(key)) return

      const state = getChatState(chatId)
      const isFirst = !state

      // First message (or "menu") always shows the menu.
      if (isFirst) {
        await client.sendText(chatId, greetingText())
        await sendMenu(client, chatId)
        setChatState(chatId, 'await_choice')
        return
      }

      if (wantsExit(messageText)) {
        chatStates.delete(chatId)
        await client.sendText(chatId, 'Thanks for using Trustify. Bye!')
        return
      }

      if (wantsMenu(messageText)) {
        await sendMenu(client, chatId)
        setChatState(chatId, 'await_choice')
        return
      }

      if (state?.step === 'await_choice') {
        const t = messageText.toLowerCase()
        const choice = t === '1' || t === 'ecommerce' || t.includes('ecom') ? 'ecom'
          : t === '2' || t === 'image' || t.includes('image') ? 'image'
          : t === '3' || t === 'news' || t.includes('news') ? 'news'
          : (t === '4' || t === 'exit' || t.includes('exit')) ? 'exit'
          : null

        if (choice === 'exit') {
          chatStates.delete(chatId)
          await client.sendText(chatId, 'Thanks for using Trustify. Bye!')
          return
        }

        if (choice === 'ecom') {
          setChatState(chatId, 'await_ecom_url')
          await client.sendText(chatId, 'Send a website URL or domain (example: amazon.in)')
          return
        }
        if (choice === 'image') {
          setChatState(chatId, 'await_image')
          await client.sendText(chatId, 'Send an image here (as a photo).')
          return
        }
        if (choice === 'news') {
          setChatState(chatId, 'await_news_query')
          await client.sendText(chatId, 'Send the news claim/headline you want to verify.')
          return
        }

        await sendMenu(client, chatId)
        return
      }

      if (state?.step === 'await_ecom_url') {
        const url = normalizeUrlInput(messageText)
        if (!url) {
          await client.sendText(chatId, 'Please send a valid website link or domain (example: https://amazon.in or amazon.in)')
          return
        }

        let reply = ''
        try {
          const data = await scanUrl(url)
          reply = formatScanReply(data, url)
        } catch (e: any) {
          const emsg = e?.response?.data?.error || e?.message || String(e)
          reply = `I couldn't scan that link right now. (${emsg})`
        }

        await client.sendText(chatId, reply)
        await sendMenu(client, chatId)
        setChatState(chatId, 'await_choice')
        return
      }

      if (state?.step === 'await_news_query') {
        const query = messageText
        if (!query) {
          await client.sendText(chatId, 'Please send a news claim/headline (text).')
          return
        }
        let reply = ''
        try {
          const data = await fetchNewsVerification(query)
          reply = formatNewsReply(data)
        } catch (e: any) {
          const emsg = e?.response?.data?.error || e?.response?.data?.detail || e?.message || String(e)
          reply = `I couldn't verify the news right now. (${emsg})`
        }

        await client.sendText(chatId, reply)
        await sendMenu(client, chatId)
        setChatState(chatId, 'await_choice')
        return
      }

      if (state?.step === 'await_image') {
        const looksLikeImage = Boolean(msg?.isMedia) || String(msg?.type || '').toLowerCase() === 'image' || String(msg?.mimetype || '').toLowerCase().startsWith('image/')
        if (!looksLikeImage) {
          await client.sendText(chatId, 'Please send an image (photo) in this chat.')
          return
        }
        let reply = ''
        try {
          const data = await analyzeImageFromMessage(client, msg)
          reply = formatImageReply(data)
        } catch (e: any) {
          reply = `I couldn't analyze that image right now. (${e?.message || String(e)})`
        }

        await client.sendText(chatId, reply)
        await sendMenu(client, chatId)
        setChatState(chatId, 'await_choice')
        return
      }

      // Safety fallback
      await sendMenu(client, chatId)
      setChatState(chatId, 'await_choice')
    } catch (e: any) {
      console.error('Auto-reply handler failed:', e?.message || String(e))
    }
  })
}

function getClient() {
  if (!clientPromise) {
    lastInitError = null

    // WPPConnect internally mutates puppeteerOptions (e.g., sets userDataDir).
    // If puppeteerOptions is undefined, some versions crash with:
    // "Cannot set properties of undefined (setting 'userDataDir')".
    const userDataDir = path.join(process.cwd(), 'wppconnect-session')
    const puppeteerOptions: any = { userDataDir }
    if (CHROME_PATH) puppeteerOptions.executablePath = CHROME_PATH

    clientPromise = wppconnect
      .create({
        session: SESSION,
        // Prevent the client from closing itself while waiting for you to scan the QR.
        // Set AUTO_CLOSE to a positive number (seconds) if you want auto-close behavior.
        autoClose: Number.isFinite(AUTO_CLOSE) && AUTO_CLOSE > 0 ? AUTO_CLOSE : (false as any),
        statusFind: (statusSession: any, session: any) => {
          lastStatus = String(statusSession)
          console.log('WPP Status:', statusSession, session)
        },
        catchQR: (base64Qrimg: string, asciiQR: string, _attempt: any, _urlCode: any) => {
          // Persist latest QR to disk for quick sharing
          const outDir = path.join(process.cwd(), 'qr')
          fs.mkdirSync(outDir, { recursive: true })
          const file = path.join(outDir, 'latest.txt')
          const data = base64Qrimg.startsWith('data:image') ? base64Qrimg : `data:image/png;base64,${base64Qrimg}`
          fs.writeFileSync(file, data)
          lastQrData = data
          // Also print ASCII QR to console as a fallback
          try { console.log("\nScan this QR (ASCII fallback):\n" + asciiQR + "\n") } catch {}
        },
        headless: HEADLESS,
        logQR: false,
        browserArgs: ['--no-sandbox','--disable-setuid-sandbox','--disable-gpu'],
        puppeteerOptions
      })
      .then((client: wppconnect.Whatsapp) => {
        console.log('WPPConnect ready')
        registerInboundHandlers(client)
        return client
      })
      .catch((e: any) => {
        const msg = e?.message ? String(e.message) : String(e)
        lastInitError = msg
        clientPromise = null
        console.error('WPPConnect init failed:', msg)
        throw e
      })
  }
  return clientPromise
}

app.get('/health', (_req: Request, res: Response) => {
  res.json({ ok: true, session: SESSION })
})

// Simple landing page to render the QR and basic actions
app.get('/', (_req: Request, res: Response) => {
  res.type('html').send(`<!doctype html>
  <html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Trustify WhatsApp</title>
    <style>
      body{font-family:system-ui,Segoe UI,Arial;background:#0b1220;color:#e2e8f0;margin:0;padding:24px}
      .card{max-width:720px;margin:0 auto;background:#0f172a;border:1px solid rgba(148,163,184,.2);border-radius:12px;padding:20px}
      .qr{display:grid;place-items:center;min-height:280px;border:1px dashed rgba(148,163,184,.3);border-radius:12px;background:#0b1329}
      img{max-width:260px;image-rendering:pixelated}
      .row{display:flex;gap:8px;margin-top:12px}
      input,button{padding:10px;border-radius:8px;border:1px solid rgba(148,163,184,.25);background:#0b1329;color:#e2e8f0}
      button{background:#2563eb;border:none;cursor:pointer}
      small{color:#94a3b8}
    </style>
  </head>
  <body>
    <div class="card">
      <h2>Trustify WhatsApp Service</h2>
      <p>Scan the QR below with WhatsApp on your phone to pair this session.</p>
      <div id="qr" class="qr">Loading QR…</div>
      <small id="status"></small>
      <script>
        async function pollQR(){
          try{
            const r = await fetch('/qr');
            if(r.status===200){
              const txt = await r.text();
              if(txt.startsWith('data:image')){
                document.getElementById('qr').innerHTML = '<img alt="QR" src="'+txt+'" />';
                document.getElementById('status').textContent = 'If the QR expires, refresh the page.';
              } else {
                document.getElementById('qr').textContent = 'QR data received but not an image.';
              }
            } else {
              const j = await r.json().catch(()=>({message:'Generating QR…'}));
              document.getElementById('qr').textContent = j.message || 'Generating QR…';
            }
          }catch(e){
            document.getElementById('qr').textContent = 'Waiting for service…';
          } finally {
            setTimeout(pollQR, 2000);
          }
        }
        pollQR();
      </script>
    </div>
  </body>
  </html>`)
})

app.get('/qr', async (_req: Request, res: Response) => {
  try {
    const file = path.join(process.cwd(), 'qr', 'latest.txt')
    if (fs.existsSync(file)) {
      const data = fs.readFileSync(file, 'utf8')
      return res.type('text/plain').send(data)
    }
    // Trigger client init to generate QR
    await getClient()
    return res.status(202).json({ message: 'QR not ready, try again shortly' })
  } catch (e: any) {
    return res.status(500).json({ error: e?.message || String(e), lastInitError })
  }
})

app.get('/status', async (_req: Request, res: Response) => {
  try {
    const file = path.join(process.cwd(), 'qr', 'latest.txt')
    const hasQR = fs.existsSync(file)
    const qrMtime = hasQR ? fs.statSync(file).mtimeMs : null
    let state: any = lastStatus
    let isAuthenticated = false
    try {
      const client = await getClient()
      const anyClient = client as any
      if (typeof anyClient.isAuthenticated === 'function') {
        isAuthenticated = await anyClient.isAuthenticated()
      }
      if (!state && typeof anyClient.getConnectionState === 'function') {
        state = await anyClient.getConnectionState()
      }
    } catch (e: any) {
      lastInitError = e?.message || String(e)
    }
    res.json({ hasQR, qrMtime, state, isAuthenticated, memoryQR: !!lastQrData, lastInitError, headless: HEADLESS, chromePathConfigured: !!CHROME_PATH })
  } catch (e: any) {
    res.status(500).json({ error: e.message })
  }
})

app.post('/send', authMiddleware, async (req: Request, res: Response) => {
  const { phone, message } = req.body as { phone?: string, message?: string }
  const targetPhone = (phone || DEFAULT_PHONE || '').trim()
  if (!targetPhone || !message) return res.status(400).json({ error: 'phone (or DEFAULT_PHONE) and message are required' })
  try {
    const client = await getClient()
    const jid = targetPhone.replace(/\D/g, '') + '@c.us'
    await client.sendText(jid, message)
    return res.json({ ok: true })
  } catch (e: any) {
    return res.status(500).json({ error: e.message })
  }
})

app.post('/scan-and-send', authMiddleware, async (req: Request, res: Response) => {
  const { url, phone } = req.body as { url?: string, phone?: string }
  const targetPhone = (phone || DEFAULT_PHONE || '').trim()
  if (!url || !targetPhone) return res.status(400).json({ error: 'url and phone (or DEFAULT_PHONE) are required' })
  try {
    const data = await scanUrl(url)
    const msg = formatScanReply(data, url)

    const client = await getClient()
  const jid = targetPhone.replace(/\D/g, '') + '@c.us'
    await client.sendText(jid, msg)

    return res.json({ ok: true, sent: true, preview: msg })
  } catch (e: any) {
    return res.status(500).json({ error: e.message })
  }
})

app.listen(PORT, () => {
  console.log(`Trustify WhatsApp server listening on :${PORT}`)
})
