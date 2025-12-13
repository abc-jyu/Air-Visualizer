// WebSocketの接続状態と拡張機能の動作状況を画面上に表示するコンポーネント
import React from "react"

interface StatusIndicatorProps {
    status: string
}

export const StatusIndicator = ({ status }: StatusIndicatorProps) => {
    return (
        <div className="fixed bottom-4 right-4 bg-gray-900 text-white p-4 rounded-lg shadow-lg z-50 opacity-80 hover:opacity-100 transition-opacity">
            <h3 className="font-bold mb-2">Air-Visualizer</h3>
            <p>Status: <span className={status.includes("Connected") ? "text-green-400" : "text-red-400"}>{status}</span></p>
            <p className="text-xs text-gray-400 mt-1">Check console for logs</p>
        </div>
    )
}
