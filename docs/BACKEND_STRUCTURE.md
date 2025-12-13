# Backend Structure Documentation

このドキュメントでは、`backend` ディレクトリ内のファイル構成と各コンポーネントの役割について説明します。

## ディレクトリ構造

```
backend/
├── app/                    # アプリケーションのメインコード
│   ├── api/                # APIエンドポイント関連
│   ├── core/               # コア設定
│   ├── models/             # データベースモデル
│   ├── services/           # ビジネスロジック
│   ├── websockets/         # WebSocket関連
│   ├── main.py             # アプリケーションのエントリーポイント
│   └── schemas.py          # Pydanticスキーマ
├── verify_db.py            # データベース検証用スクリプト
└── verify_transcript.py    # API検証用スクリプト
```

## ファイル詳細

### `app/`

アプリケーションの主要なソースコードが含まれています。

#### `app/main.py`
FastAPIアプリケーションのエントリーポイントです。
- アプリケーションの初期化 (`FastAPI`)
- データベースの初期化 (`startup` イベント)
- ルーターの組み込み (`websockets`)
- 基本的なHTTPエンドポイントの実装 (`/`, `/transcripts`)

#### `app/schemas.py`
Pydanticを使用したデータバリデーションスキーマを定義しています。
- `TranscriptCreate`: トランスクリプト作成時の入力データ構造 (speaker, text, timestamp)

### `app/core/`

#### `app/core/config.py`
アプリケーションの設定管理を行います。
- `Settings` クラス: プロジェクト名、バージョン、APIプレフィックスなどの定数を管理します。

### `app/models/`

SQLAlchemyを使用したデータベースモデルを定義しています。

#### `app/models/session.py`
データベース接続とセッション管理を行います。
- `AsyncSessionLocal`: 非同期データベースセッションファクトリ
- `init_db`: データベーステーブルの作成
- `get_db`: セッション依存性注入用関数

#### `app/models/transcript.py`
トランスクリプト（議事録）のデータモデルです。
- `Transcript` クラス: `transcripts` テーブルに対応し、`id`, `speaker`, `text`, `timestamp` カラムを持ちます。

### `app/websockets/`

リアルタイム通信を扱うWebSocket関連のコードです。

#### `app/websockets/manager.py`
WebSocket接続の管理を行います。
- `ConnectionManager` クラス: アクティブな接続のリスト管理、接続・切断処理、ブロードキャスト機能を提供します。

#### `app/websockets/router.py`
WebSocketのルーティングとメッセージ処理ロジックです。
- `/ws` エンドポイント: クライアントからの接続を受け付けます。
- メッセージ受信時の処理:
    1. 受信データのJSONパース
    2. データベースへの保存 (`Transcript` モデル)
    3. 分析サービスへの送信 (プレースホルダー)
    4. コーチングサービスへの送信 (プレースホルダー)
    5. クライアントへの結果ブロードキャスト

### `app/services/`

ビジネスロジックや外部サービス連携を行うモジュールです。

#### `app/services/analysis/`
- `audio.py`: 音声分析ロジック（現在はプレースホルダー）
- `sentiment.py`: 感情分析ロジック（現在はプレースホルダー）

#### `app/services/coaching/`
- `llm.py`: LLMを使用したコーチング生成ロジック（現在はプレースホルダー）

### ルートディレクトリ

#### `verify_db.py`
データベースに保存されたトランスクリプトを確認するためのユーティリティスクリプトです。
- 保存されている全トランスクリプトを取得して表示します。

#### `verify_transcript.py`
`/transcripts` エンドポイントに対してPOSTリクエストを送信し、APIの動作確認を行うためのスクリプトです。
