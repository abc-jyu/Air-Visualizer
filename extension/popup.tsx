import { useEffect, useMemo, useState } from "react"

type ConnState = "connected" | "connecting" | "disconnected"

type StatusPayload = {
  conn: ConnState
  airScore: number 
  airLabel: string 
  captions: string[]
  lastUpdated?: number
}

const clamp01 = (x: number) => Math.max(0, Math.min(1, x))

const styles: Record<string, any> = {
  root: { padding: 16, width: 360, fontFamily: "system-ui" },
  header: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 },
  h1: { fontSize: 16, fontWeight: 900, margin: 0 },
  sub: { fontSize: 12, color: "#6b7280", margin: "4px 0 0" },

  card: { border: "1px solid #e5e7eb", borderRadius: 14, padding: 12, marginTop: 12, background: "white" },
  title: { fontSize: 13, fontWeight: 900, margin: 0 },
  caption: { fontSize: 12, color: "#6b7280", margin: "6px 0 0" },

  row: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, marginTop: 10 },

  dot: (s: ConnState) => ({
    width: 10,
    height: 10,
    borderRadius: 999,
    background: s === "connected" ? "#22c55e" : s === "connecting" ? "#f59e0b" : "#ef4444"
  }),
  badge: { display: "flex", alignItems: "center", gap: 8, fontSize: 12, fontWeight: 800 },

  meterBar: { height: 10, background: "#e5e7eb", borderRadius: 999, overflow: "hidden", marginTop: 10 },
  meterFill: (p: number) => ({ height: "100%", width: `${Math.round(p * 100)}%`, background: "#111827" }),
  meterLabels: { display: "flex", justifyContent: "space-between", fontSize: 11, color: "#6b7280", marginTop: 6 },

  btnRow: { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 },
  btn: {
    border: "1px solid #e5e7eb",
    borderRadius: 12,
    padding: "8px 10px",
    background: "white",
    cursor: "pointer",
    fontSize: 12,
    fontWeight: 800
  },

  logBox: {
    marginTop: 10,
    height: 170,
    overflow: "auto",
    background: "#0b1220",
    color: "#d1d5db",
    borderRadius: 12,
    padding: 10,
    fontSize: 12,
    lineHeight: 1.35
  },
  faint: { opacity: 0.7 }
}

function labelFromScore(score01: number) {
  const x = clamp01(score01)
  if (x < 0.33) return "緊迫"
  if (x < 0.66) return "普通"
  return "和やか"
}

async function send<T = any>(msg: any): Promise<T | null> {
  try {
    const res = await chrome.runtime.sendMessage(msg)
    return res ?? null
  } catch {
    return null
  }
}

export default function Popup() {
  const [status, setStatus] = useState<StatusPayload>({
    conn: "disconnected",
    airScore: 0,
    airLabel: "不明",
    captions: []
  })
  const [showLogs, setShowLogs] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const airPct = useMemo(() => clamp01(status.airScore), [status.airScore])
  const airLabel = useMemo(
    () => (status.airLabel && status.airLabel !== "不明" ? status.airLabel : labelFromScore(status.airScore)),
    [status.airLabel, status.airScore]
  )

  const colorFromPct = (p: number) => {
    const v = clamp01(p)
   
    if (v < 0.5) {
      const t = v / 0.5
     
      const r1 = 0xef, g1 = 0x44, b1 = 0x44
      const r2 = 0xf5, g2 = 0x9e, b2 = 0x0b
      const ri = Math.round(r1 + (r2 - r1) * t)
      const gi = Math.round(g1 + (g2 - g1) * t)
      const bi = Math.round(b1 + (b2 - b1) * t)
      return `rgb(${ri}, ${gi}, ${bi})`
    }
    const t = (v - 0.5) / 0.5
  
    const r1 = 0xf5, g1 = 0x9e, b1 = 0x0b
    const r2 = 0x22, g2 = 0xc5, b2 = 0x5e
    const ri = Math.round(r1 + (r2 - r1) * t)
    const gi = Math.round(g1 + (g2 - g1) * t)
    const bi = Math.round(b1 + (b2 - b1) * t)
    return `rgb(${ri}, ${gi}, ${bi})`
  }


  useEffect(() => {
    let alive = true

    const tick = async () => {
      const res = await send<{ ok: boolean; data?: StatusPayload }>({ type: "GET_STATUS" })
      if (!alive) return
      if (res?.ok && res.data) setStatus(res.data)
    }

    tick()

    if (!autoRefresh) return () => void (alive = false)

    const id = window.setInterval(tick, 800)
    return () => {
      alive = false
      window.clearInterval(id)
    }
  }, [autoRefresh])

  
  useEffect(() => {
    const handler = (msg: any) => {
      if (msg?.type === "STATUS_PUSH" && msg.data) {
        setStatus(msg.data as StatusPayload)
      }
    }
    chrome.runtime.onMessage.addListener(handler)
    return () => chrome.runtime.onMessage.removeListener(handler)
  }, [])

  return (
    <div style={styles.root}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.h1}>Air Visualizer</h1>
          <p style={styles.sub}>システムの状態と「場の空気」を可視化</p>
        </div>
        <div style={styles.badge}>
          <div style={styles.dot(status.conn)} />
          <span>
            {status.conn === "connected" ? "Connected" : status.conn === "connecting" ? "Connecting" : "Disconnected"}
          </span>
        </div>
      </div>

      <div style={styles.card}>
        <h2 style={styles.title}>接続ステータス</h2>
        <p style={styles.caption}>WebSocket（バックエンド）との接続状況</p>

        <div style={styles.btnRow}>
          <button style={styles.btn} onClick={() => send({ type: "RECONNECT_WS" })}>
            再接続
          </button>
          <button
            style={styles.btn}
            onClick={async () => {
              const res = await send<{ ok: boolean; data?: StatusPayload }>({ type: "GET_STATUS" })
              if (res?.ok && res.data) setStatus(res.data)
            }}>
            更新
          </button>
          <button style={styles.btn} onClick={() => setAutoRefresh((v) => !v)}>
            自動更新: {autoRefresh ? "ON" : "OFF"}
          </button>
        </div>

        {status.lastUpdated ? (
          <div style={{ ...styles.caption, marginTop: 10 }}>
            最終更新: {new Date(status.lastUpdated).toLocaleTimeString()}
          </div>
        ) : null}
      </div>

      <div style={styles.card}>
        <h2 style={styles.title}>「空気」メーター</h2>
        <p style={styles.caption}>緊迫 ↔ 和やか（スコアは 0〜1）</p>

        <div style={styles.meterBar}>
          <div
            style={{
              height: "100%",
              width: `${Math.round(airPct * 100)}%`,
              background: colorFromPct(airPct),
              transition: "width 250ms ease, background 250ms ease"
            }}
          />
        </div>

        <div style={styles.meterLabels}>
          <span>緊迫</span>
          <span style={{ color: "#111827", fontWeight: 900 }}>{airLabel}</span>
          <span>和やか</span>
        </div>

        <div style={{ ...styles.caption, marginTop: 8 }}>
          スコア: {airPct.toFixed(2)}
        </div>
      </div>

      <div style={styles.card}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "baseline" }}>
          <div>
            <h2 style={styles.title}>デバッグログ（字幕）</h2>
            <p style={styles.caption}>抽出された字幕を表示（検証用）</p>
          </div>
          <button style={styles.btn} onClick={() => setShowLogs((v) => !v)}>
            {showLogs ? "ログを折りたたむ" : "ログを表示"}
          </button>
        </div>

        {showLogs && (
          <>
            <div style={styles.btnRow}>
              <button style={styles.btn} onClick={() => send({ type: "CLEAR_LOGS" })}>
                クリア
              </button>
              <button style={styles.btn} onClick={() => send({ type: "TOGGLE_CAPTION_CAPTURE" })}>
                取得切替
              </button>
            </div>

            <div style={styles.logBox}>
              {status.captions.length === 0 ? (
                <div style={styles.faint}>まだ字幕がありません（Meetで字幕ON & content script動作を確認）</div>
              ) : (
                status.captions.slice(-300).map((line, i) => <div key={i}>{line}</div>)
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}