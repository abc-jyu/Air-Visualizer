# Extension Structure Documentation

このドキュメントでは、`extension` ディレクトリ内のファイル構成と各コンポーネントの役割について説明します。この拡張機能は [Plasmo](https://docs.plasmo.com/) フレームワークを使用して構築されています。

## ディレクトリ構造

```
extension/
├── assets/                 # アイコンなどの静的アセット
├── build/                  # ビルド成果物 (Plasmoによって生成)
├── components/             # Reactコンポーネント
├── contents/               # Content Scripts (Webページ上で実行されるスクリプト)
├── hooks/                  # カスタムReactフック
├── node_modules/           # 依存パッケージ
├── package.json            # プロジェクト設定と依存関係
├── popup.tsx               # ポップアップUI (ツールバーアイコンクリック時)
└── tsconfig.json           # TypeScript設定
```

## ファイル詳細

### ルートディレクトリ

#### `package.json`
プロジェクトの設定ファイルです。
- Plasmoのスクリプト (`dev`, `build`, `package`)
- 依存関係 (`plasmo`, `react`, `react-dom` など)
- `manifest` 設定: 権限 (`https://meet.google.com/*`) などを定義します。

#### `popup.tsx`
拡張機能のアイコンをクリックした際に表示されるポップアップ画面のUIです。
- 現在はPlasmoのデフォルトのWelcomeメッセージと入力フィールドを表示しています。

### `contents/`

Webページ（Google Meet）のコンテキストで実行されるスクリプトです。

#### `contents/meet-observer.tsx`
Google Meetページで実行されるメインのContent Scriptです。
- `config`: 実行対象のURLパターン (`https://meet.google.com/*`) を定義。
- `MeetObserver`: メインコンポーネント。WebSocket接続と字幕監視フックを初期化し、ステータスインジケーターを表示します。

### `components/`

再利用可能なUIコンポーネントです。

#### `components/StatusIndicator.tsx`
画面右下に表示されるステータスインジケーターです。
- WebSocketの接続状態（Connected, Disconnected, Error）を表示します。

### `hooks/`

ロジックをカプセル化したカスタムフックです。

#### `hooks/useWebSocket.ts`
WebSocket接続を管理するフックです。
- 指定されたURL（`ws://localhost:8000/ws`）への接続を確立します。
- 接続状態 (`status`) と WebSocket インスタンス (`ws`) を提供します。
- 自動再接続ロジックは現在は含まれていません（切断時は `Disconnected` 状態になります）。

#### `hooks/useTranscriptObserver.ts`
Google Meetの字幕DOMを監視し、テキストを抽出する核心的なロジックです。
- `MutationObserver` を使用して字幕コンテナの変更を検知します。
- 字幕の構造（話者名とテキスト）を解析します。
- バッファリング機能: 同じ話者の発言が続いている間はバッファに溜め、話者が変わるか一定のタイミングでWebSocket経由でバックエンドに送信します。
