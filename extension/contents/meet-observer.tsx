// Google Meetの字幕を監視し、WebSocket経由でバックエンドに送信するメインコンポーネント
import type { PlasmoCSConfig } from "plasmo"

import { StatusIndicator } from "../components/StatusIndicator"
import { useTranscriptObserver } from "../hooks/useTranscriptObserver"
import { useWebSocket } from "../hooks/useWebSocket"

export const config: PlasmoCSConfig = {
    matches: ["https://meet.google.com/*"]
}

const MeetObserver = () => {
    const { ws, status, setStatus } = useWebSocket("ws://localhost:8000/ws")

    useTranscriptObserver(ws, status, setStatus)

    return <StatusIndicator status={status} />
}

export default MeetObserver
