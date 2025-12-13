// WebSocket接続の管理とステータス状態を提供するカスタムフック
import { useEffect, useState } from "react"

export const useWebSocket = (url: string) => {
    const [ws, setWs] = useState<WebSocket | null>(null)
    const [status, setStatus] = useState("Disconnected")

    useEffect(() => {
        const socket = new WebSocket(url)

        socket.onopen = () => {
            console.log("Connected to WebSocket")
            setStatus("Connected")
        }

        socket.onclose = () => {
            console.log("Disconnected from WebSocket")
            setStatus("Disconnected")
        }

        socket.onerror = (error) => {
            console.error("WebSocket error:", error)
            setStatus("Error")
        }

        setWs(socket)

        return () => {
            socket.close()
        }
    }, [url])

    return { ws, status, setStatus }
}
