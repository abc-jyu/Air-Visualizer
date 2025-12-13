# 環境構築ガイド

このプロジェクトでは、開発環境の管理に [mise](https://mise.jdx.dev/) を使用しています。
`mise` を使用することで、Python, Node.js, uv などのツールやランタイムのバージョンをプロジェクトごとに自動的に管理できます。

## 1. 前提条件

以下のツールがインストールされている必要があります。

*   `curl` (mise のインストールに使用)
*   `git` (リポジトリのクローンに使用)

## 2. mise のインストール

まだ `mise` をインストールしていない場合は、以下のコマンドでインストールしてください。

```bash
curl https://mise.run | sh
```

インストール後、シェルの設定ファイル（`.bashrc`, `.zshrc` など）にパスを通す必要があります。詳細は [mise の公式ドキュメント](https://mise.jdx.dev/getting-started.html) を参照してください。

例 (zsh の場合):
```bash
echo 'eval "$(~/.local/bin/mise activate zsh)"' >> ~/.zshrc
source ~/.zshrc
```

## 3. プロジェクトのセットアップ

リポジトリをクローンし、プロジェクトディレクトリに移動した後、以下のコマンドを実行して環境を構築します。

### 3.1. リポジトリのクローン

以下のコマンドでリポジトリをクローンし、ディレクトリに移動します。

```bash
git clone https://github.com/abc-jyu/Air-Visualizer.git
cd Air-Visualizer
```

### 3.2. ツールのインストール

`mise.toml` に定義されたツール (Python, Node.js, uv) をインストールします。

```bash
mise install
```

> **Note**
> `uv` もこのコマンドで自動的にインストールされます。個別にインストールする必要はありません。

### 3.3. 依存関係のインストール

プロジェクトの依存パッケージ (Python ライブラリ, npm パッケージ) をインストールします。

```bash
mise run setup
```

このコマンドは内部で以下を実行します：
*   `backend/`: `uv pip install -r requirements.txt`
*   `extension/`: `pnpm install`

## 4. アプリケーションの起動

### バックエンド (FastAPI)

以下のコマンドでバックエンドサーバーを起動します。

```bash
mise run start:backend
```

サーバーは `http://127.0.0.1:8000` で起動し、ホットリロードが有効になります。

### 拡張機能 (Plasmo)

以下のコマンドで拡張機能の開発サーバーを起動します。

```bash
mise run start:extension
```

### 4.2. ブラウザへの読み込み

1.  Google Chrome で `chrome://extensions` を開きます。
2.  右上の「デベロッパーモード (Developer mode)」をオンにします。
3.  左上の「パッケージ化されていない拡張機能を読み込む (Load unpacked)」をクリックします。
4.  プロジェクト内の `extension/build/chrome-mv3-dev` ディレクトリを選択します。

これで拡張機能がブラウザに読み込まれ、使用可能になります。コードを変更した際は、自動的に再ビルドされますが、ブラウザへの反映には拡張機能の再読み込み（リロードボタン）が必要な場合があります。

## 5. トラブルシューティング

### コマンドが見つからない場合

`mise` 経由でインストールしたツールが認識されない場合は、一度シェルを再起動するか、`mise reshim` を実行してみてください。

### 依存関係のインストールに失敗する場合

`mise install` が正常に完了しているか確認してください。特定のツールのバージョンが正しくインストールされていない可能性があります。
