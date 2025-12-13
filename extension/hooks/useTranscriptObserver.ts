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
                console.log(`Air-Visualizer: Sending:`, JSON.stringify(data))
                ws.send(JSON.stringify(data))
            }
        }

        const observerCallback = (mutations: MutationRecord[]) => {
            mutations.forEach((mutation) => {
                if (mutation.type === "characterData") {
                    const target = mutation.target as Node
                    const parentElement = target.parentElement

                    // Logic ported from transcriptonic
                    // Structure: <div>(Name)</div><div>(Text)</div>
                    // mutation.target is the Text Node inside the second div.
                    // parentElement is the second div.
                    // previousSibling is the first div (Name).
                    const currentPersonName = parentElement?.previousSibling?.textContent
                    const currentTranscriptText = parentElement?.textContent

                    if (currentPersonName && currentTranscriptText) {
                        // Starting fresh in a meeting or new block
                        if (!transcriptTargetBuffer.current) {
                            transcriptTargetBuffer.current = parentElement
                            personNameBuffer.current = currentPersonName
                            timestampBuffer.current = new Date().toISOString()
                            transcriptTextBuffer.current = currentTranscriptText
                        }
                        // Some prior transcript buffer exists
                        else {
                            // New transcript UI block
                            if (transcriptTargetBuffer.current !== parentElement) {
                                // Push previous transcript block (final update for that block)
                                pushBufferToTranscript()

                                // Update buffers for next mutation
                                transcriptTargetBuffer.current = parentElement
                                personNameBuffer.current = currentPersonName
                                timestampBuffer.current = new Date().toISOString()
                                transcriptTextBuffer.current = currentTranscriptText
                            }
                            // Same transcript UI block being appended
                            else {
                                // Update buffer for next mutation
                                transcriptTextBuffer.current = currentTranscriptText
                            }
                        }

                        // Log to indicate that the extension is working (similar to transcriptonic)
                        if (transcriptTextBuffer.current) {
                            console.log(`Air-Visualizer: Current Buffer:`, JSON.stringify({
                                speaker: personNameBuffer.current,
                                text: transcriptTextBuffer.current
                            }))
                        }
                    }
                }
            })
        }

        const observer = new MutationObserver(observerCallback)

        const findTranscriptContainer = () => {
            const transcriptContainer = document.querySelector('div[role="region"][tabindex="0"]')
            if (transcriptContainer) {
                console.log("Air-Visualizer: Transcript container found!", transcriptContainer)
                // Only update status if it's not already "Connected & Listening" to avoid re-renders loop if we were to add it to dependency
                setStatus((prev) => prev === "Connected" ? "Connected & Listening" : prev)

                observer.observe(transcriptContainer, {
                    childList: true,
                    attributes: true,
                    subtree: true,
                    characterData: true
                })
            } else {
                console.log("Air-Visualizer: Transcript container NOT found, retrying...")
                setTimeout(findTranscriptContainer, 2000)
            }
        }

        findTranscriptContainer()

        return () => {
            observer.disconnect()
            // Push any remaining buffer when disconnecting (e.g. meeting end)
            pushBufferToTranscript()
        }
    }, [ws, status, setStatus])
}
