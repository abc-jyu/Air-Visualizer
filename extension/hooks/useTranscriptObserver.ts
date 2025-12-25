// MutationObserverを使用してDOMの変化を監視し、字幕データを抽出・バッファリングするカスタムフック
import { useEffect, useRef } from "react"

export const useTranscriptObserver = (
    ws: WebSocket | null,
    status: string,
    setStatus: (status: string | ((prev: string) => string)) => void
) => {
    // Buffer refs to hold transcript data between mutations
    const transcriptTargetBuffer = useRef<Node | null>(null)
    const personNameBuffer = useRef<string>("")
    const transcriptTextBuffer = useRef<string>("")
    const timestampBuffer = useRef<string>("")

    useEffect(() => {
        if (!ws || status === "Disconnected" || status === "Error") return

        const pushBufferToTranscript = () => {
            if (personNameBuffer.current && transcriptTextBuffer.current) {
                const data = {
                    speaker: personNameBuffer.current,
                    text: transcriptTextBuffer.current,
                    timestamp: timestampBuffer.current
                }
                try {
                    console.log(`Air-Visualizer: Sending:`, JSON.stringify(data))
                    ws.send(JSON.stringify(data))
                } catch (e) {
                    console.warn("Air-Visualizer: Failed to send ws message", e)
                }
            }
        }

        
        let remoteSelectors: string[] = []
        const tryFetchSelectors = async () => {
            try {
                const controller = new AbortController()
                const id = setTimeout(() => controller.abort(), 2000)
                const res = await fetch("http://localhost:8000/config", { signal: controller.signal })
                clearTimeout(id)
                if (res.ok) {
                    const j = await res.json()
                    if (Array.isArray(j.selectors)) remoteSelectors = j.selectors
                }
            } catch (e) {
                
            }
        }

       
        const defaultSelectors = [
            'div[role="region"][tabindex="0"]',
            'div[aria-label*="captions"]',
            'div[jsname] > div[jsname]',
            'div[role="list"]'
        ]

        const combinedSelectors = () => [...remoteSelectors, ...defaultSelectors]

        const observerCallback = (mutations: MutationRecord[]) => {
            const processNode = (node: Node | null) => {
                if (!node) return
                const el = node instanceof Element ? node : node.parentElement
                if (!el) return
                
                const maybeSpeaker = el.previousElementSibling?.textContent?.trim() || el.querySelector?.("[data-speaker]")?.textContent?.trim()
                const maybeText = el.textContent?.trim()
                if (maybeText && maybeSpeaker && maybeSpeaker.length < 60) {
                   
                    if (!transcriptTargetBuffer.current || transcriptTargetBuffer.current !== el) {
                        pushBufferToTranscript()
                        transcriptTargetBuffer.current = el
                        personNameBuffer.current = maybeSpeaker
                        timestampBuffer.current = new Date().toISOString()
                        transcriptTextBuffer.current = maybeText
                    } else {
                       
                        transcriptTextBuffer.current = maybeText
                    }
                    console.log("Air-Visualizer: Current Buffer:", { speaker: personNameBuffer.current, text: transcriptTextBuffer.current })
                }
            }

            for (const m of mutations) {
                if (m.type === "characterData") {
                    processNode(m.target as Node)
                }
                if (m.type === "childList") {
                    m.addedNodes.forEach((n) => processNode(n))
                }
            }
        }

        const observer = new MutationObserver(observerCallback)

        const findTranscriptContainer = async () => {
            await tryFetchSelectors()

            const selectors = combinedSelectors()

            for (const sel of selectors) {
                try {
                    const node = document.querySelector(sel)
                    if (node) {
                        console.log("Air-Visualizer: Transcript container found via selector:", sel, node)
                        setStatus((prev) => (prev === "Connected" ? "Connected & Listening" : prev))
                        observer.observe(node, { childList: true, attributes: false, subtree: true, characterData: true })
                        return
                    }
                } catch (e) {
                   
                    continue
                }
            }

 
            const allDivs = Array.from(document.querySelectorAll("div"))
            for (const d of allDivs) {
                const txt = d.textContent?.trim() || ""
                if (!txt) continue
              
                const lines = txt.split(/\n|\r|\.|。|、/).map((s) => s.trim()).filter(Boolean)
                if (lines.length >= 3 && lines.some((l) => l.length < 120)) {
                    console.log("Air-Visualizer: Transcript container heuristically found", d)
                    setStatus((prev) => (prev === "Connected" ? "Connected & Listening" : prev))
                    observer.observe(d, { childList: true, attributes: false, subtree: true, characterData: true })
                    return
                }
            }

          
            console.log("Air-Visualizer: Transcript container NOT found, retrying...")
            setTimeout(findTranscriptContainer, 2000)
        }

        findTranscriptContainer()

        return () => {
            observer.disconnect()
            pushBufferToTranscript()
        }
    }, [ws, status, setStatus])
}
