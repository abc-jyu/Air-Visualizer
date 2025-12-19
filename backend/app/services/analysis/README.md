# Analysis Services - 使い方ガイド

Air-Visualizerの感情分析・音声分析サービスの使用方法をまとめたドキュメントです。

## 📋 目次

- [概要](#概要)
- [感情分析 (sentiment.py)](#感情分析-sentimentpy)
- [音声分析 (audio.py)](#音声分析-audiopy)
- [WebSocket統合](#websocket統合)
- [トラブルシューティング](#トラブルシューティング)

---

## 概要

このモジュールは以下の2つの主要な機能を提供します：

1. **感情分析**: 日本語テキストから8つの感情スコアを抽出
2. **音声分析**: 音声データから音量とピッチを抽出

### 使用モデル・ライブラリ

- **感情分析**: `neuralnaut/deberta-wrime-emotions` (DeBERTa + WRIME dataset)
- **音声分析**: Librosa (音響特徴量抽出)
- **実行環境**: CPU推論（GPU不要）

---

## 感情分析 (sentiment.py)

### 概要

日本語テキストから8つの感情スコアを抽出します。WRIME（Writers and Readers Emotion）データセットで学習済みのDeBERTaモデルを使用します。

### 感情カテゴリ

以下の8つの感情について、それぞれ0.0〜1.0のスコアを返します：

| 日本語 | 英語 | 説明 |
|--------|------|------|
| 喜び | Joy | ポジティブな感情 |
| 悲しみ | Sadness | ネガティブな感情 |
| 期待 | Anticipation | 将来への期待 |
| 驚き | Surprise | 予期しない出来事 |
| 怒り | Anger | 不満や憤り |
| 恐れ | Fear | 不安や恐怖 |
| 嫌悪 | Disgust | 嫌な感情 |
| 信頼 | Trust | 信頼感 |

### 初期化

アプリケーション起動時に自動的に初期化されます（`main.py`のstartupイベント）。

```python
from app.services.analysis.sentiment import initialize_sentiment_model

# 起動時に1回だけ実行
await initialize_sentiment_model()
```

**初期化時の動作:**
- HuggingFace Hubからモデルをダウンロード（初回のみ）
- モデルをメモリにロード（約500MB）
- CPUモードで実行
- スレッド数を4に設定

### 使用方法

#### 基本的な使い方

```python
from app.services.analysis.sentiment import analyze_sentiment

# テキストを分析
text = "今日はとても嬉しいです！"
result = await analyze_sentiment(text)

# 結果
# {
#     "喜び": 0.75,
#     "悲しみ": 0.05,
#     "期待": 0.10,
#     "驚き": 0.05,
#     "怒り": 0.02,
#     "恐れ": 0.01,
#     "嫌悪": 0.01,
#     "信頼": 0.01
# }
```

#### WebSocket経由での使用

```python
from app.services.analysis.sentiment import analyze_sentiment

# WebSocketハンドラー内で
text = data_json.get("text", "")
sentiment_result = await analyze_sentiment(text)

# クライアントに送信
response = {
    "type": "analysis_result",
    "sentiment": sentiment_result
}
await websocket.send_json(response)
```

### 入出力仕様

#### 入力

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `text` | `str` | ✓ | 分析対象の日本語テキスト |

**制約:**
- 最大長: 512トークン（約500-600文字）
- 超過分は自動的に切り詰め
- 空文字列の場合は全て0.0を返す

#### 出力

```python
Dict[str, float]
```

8つの感情それぞれのスコア（0.0〜1.0）を含む辞書。各スコアはsoftmax関数で正規化されており、合計は約1.0になります。

### エラーハンドリング

```python
try:
    result = await analyze_sentiment(text)
except RuntimeError as e:
    # モデルが初期化されていない場合
    print(f"Model not initialized: {e}")
except Exception as e:
    # その他のエラー（推論失敗など）
    # 自動的に全て0.0のスコアを返す
    print(f"Analysis error: {e}")
```

### パフォーマンス

- **CPU推論時間**: 約0.5〜2秒/テキスト
- **メモリ使用量**: 約500MB（モデル）
- **同時実行**: asyncio.to_thread()により、イベントループをブロックしない

### 使用例

#### 例1: ポジティブなテキスト

```python
text = "今日の試験に合格しました！本当に嬉しいです！"
result = await analyze_sentiment(text)
# 期待される結果: 喜び > 0.5, 期待 > 0.2
```

#### 例2: ネガティブなテキスト

```python
text = "大切なものを失ってしまって、とても悲しいです。"
result = await analyze_sentiment(text)
# 期待される結果: 悲しみ > 0.5
```

#### 例3: 感情の強弱を判定

```python
result = await analyze_sentiment(text)

# 最も強い感情を取得
dominant_emotion = max(result, key=result.get)
dominant_score = result[dominant_emotion]

if dominant_score > 0.5:
    print(f"強い{dominant_emotion}を検出: {dominant_score:.2f}")
```

---

## 音声分析 (audio.py)

### 概要

音声データから音響特徴量（音量・ピッチ）を抽出します。Librosaを使用して、感情分析の補正値として利用します。

### 抽出する特徴量

| 特徴量 | 説明 | 範囲 | 用途 |
|--------|------|------|------|
| **volume** | 音量（RMS energy） | 0.0〜1.0 | 声の大きさ |
| **pitch** | ピッチ（基本周波数） | Hz（通常50〜500） | 声の高さ |

### 対応フォーマット

以下の音声フォーマットに対応しています：

| フォーマット | 拡張子 | 備考 |
|-------------|--------|------|
| WebM | `.webm` | Chrome MediaRecorder APIの標準出力 |
| WAV | `.wav` | 非圧縮、最も処理が高速 |
| MP3 | `.mp3` | 圧縮形式 |
| OGG | `.ogg` | オープンソース圧縮形式 |
| M4A | `.m4a` | AAC圧縮 |

**注意**: WebM/MP3/OGGの処理にはFFmpegが必要です。

### 使用方法

#### 基本的な使い方

```python
from app.services.analysis.audio import analyze_audio

# 音声データ（bytes）を分析
audio_bytes = b'...'  # 音声ファイルのバイナリデータ
result = await analyze_audio(audio_bytes, format_hint="webm")

# 結果
# {
#     "volume": 0.65,  # 0.0〜1.0の範囲
#     "pitch": 220.5   # Hz単位
# }
```

#### WebSocket経由での使用（Base64エンコード）

```python
import base64
from app.services.analysis.audio import analyze_audio

# Base64デコード
audio_base64 = data_json.get("audio")
audio_format = data_json.get("audio_format", "webm")

if audio_base64:
    audio_bytes = base64.b64decode(audio_base64)
    audio_result = await analyze_audio(audio_bytes, audio_format)

    # 結果を使用
    if audio_result["volume"] > 0.7 and audio_result["pitch"] > 300:
        print("大声で高い声 → 怒りの可能性")
```

### 入出力仕様

#### 入力

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `audio_bytes` | `bytes` | ✓ | 音声データのバイナリ |
| `format_hint` | `Optional[str]` | - | フォーマットヒント（'webm', 'wav', 'mp3'等） |

**format_hint省略時の動作:**
- マジックバイトから自動判定
- 判定できない場合はWebMとして処理

#### 出力

```python
Dict[str, float]
```

| キー | 型 | 説明 |
|------|-----|------|
| `volume` | `float` | 音量（0.0〜1.0） |
| `pitch` | `float` | ピッチ（Hz、通常50〜500） |

### 音量 (Volume) の解釈

音量はRMS（Root Mean Square）エネルギーを0〜1の範囲に正規化した値です。

| 範囲 | 解釈 | 例 |
|------|------|-----|
| 0.0〜0.3 | 小さい声 | ささやき、静かな会話 |
| 0.3〜0.6 | 普通の声 | 通常の会話 |
| 0.6〜0.8 | 大きい声 | 大声での会話 |
| 0.8〜1.0 | 非常に大きい声 | 叫び声、怒鳴り声 |

### ピッチ (Pitch) の解釈

ピッチは基本周波数（F0）をHz単位で表します。

| 範囲（Hz） | 解釈 | 例 |
|-----------|------|-----|
| 50〜150 | 低い声 | 男性の低音 |
| 150〜250 | 普通の声（男性） | 通常の男性の声 |
| 200〜350 | 普通の声（女性） | 通常の女性の声 |
| 350〜500+ | 高い声 | 女性の高音、感情的な声 |

### エラーハンドリング

```python
try:
    result = await analyze_audio(audio_bytes, "webm")
except Exception as e:
    # エラー時は自動的に0.0を返す
    # {"volume": 0.0, "pitch": 0.0}
    print(f"Audio analysis error: {e}")
```

**一般的なエラー:**
- フォーマット不正
- ファイル破損
- FFmpeg未インストール（WebM/MP3の場合）

### パフォーマンス

- **処理時間**: 約0.5〜3秒/5秒の音声
- **メモリ使用量**: 約50〜100MB（一時ファイル含む）
- **一時ファイル**: 自動的にクリーンアップされる

### 使用例

#### 例1: 感情分析との組み合わせ

```python
# テキストと音声の両方を分析
sentiment = await analyze_sentiment(text)
audio = await analyze_audio(audio_bytes, "webm")

# 音声特徴で感情を補正
if audio["volume"] > 0.7 and audio["pitch"] > 300:
    # 大声＋高音 → 怒りの可能性
    if sentiment["怒り"] > 0.3:
        print("怒りを検出（音声特徴で確認済み）")

elif audio["volume"] < 0.3 and audio["pitch"] < 200:
    # 小声＋低音 → 悲しみの可能性
    if sentiment["悲しみ"] > 0.3:
        print("悲しみを検出（音声特徴で確認済み）")
```

#### 例2: 音声の前処理

```python
# ファイルから読み込み
with open("audio.webm", "rb") as f:
    audio_bytes = f.read()

result = await analyze_audio(audio_bytes, "webm")
print(f"Volume: {result['volume']:.2f}")
print(f"Pitch: {result['pitch']:.1f} Hz")
```

#### 例3: ヘルスチェック

```python
from app.services.analysis.audio import test_audio_processing

# 音声処理ライブラリの動作確認
is_ok = await test_audio_processing()
if is_ok:
    print("✓ Audio processing is ready")
else:
    print("✗ Audio processing failed")
```

---

## WebSocket統合

### エンドポイント

```
ws://127.0.0.1:8000/ws
```

### リクエスト形式

```json
{
  "speaker": "ユーザー名",
  "text": "今日はとても嬉しいです！",
  "timestamp": "2025-12-19T12:00:00Z",
  "audio": "Base64エンコードされた音声データ（オプション）",
  "audio_format": "webm"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `speaker` | `string` | ✓ | 話者名 |
| `text` | `string` | ✓ | 分析対象のテキスト |
| `timestamp` | `string` | - | ISO 8601形式のタイムスタンプ |
| `audio` | `string` | - | Base64エンコードされた音声データ |
| `audio_format` | `string` | - | 音声フォーマット（デフォルト: "webm"） |

### レスポンス形式

```json
{
  "type": "analysis_result",
  "transcript_id": 1,
  "speaker": "ユーザー名",
  "text": "今日はとても嬉しいです！",
  "timestamp": "2025-12-19T12:00:00Z",
  "sentiment": {
    "喜び": 0.75,
    "悲しみ": 0.05,
    "期待": 0.10,
    "驚き": 0.05,
    "怒り": 0.02,
    "恐れ": 0.01,
    "嫌悪": 0.01,
    "信頼": 0.01
  },
  "audio": {
    "volume": 0.65,
    "pitch": 220.5
  }
}
```

### エラーレスポンス

```json
{
  "type": "error",
  "message": "エラーメッセージ"
}
```

### JavaScript実装例

```javascript
// WebSocket接続
const ws = new WebSocket('ws://127.0.0.1:8000/ws');

// テキストのみ送信
ws.send(JSON.stringify({
  speaker: "ユーザー",
  text: "今日はとても嬉しいです",
  timestamp: new Date().toISOString()
}));

// テキスト + 音声を送信
const audioBlob = await recorder.stop();
const audioBase64 = await blobToBase64(audioBlob);

ws.send(JSON.stringify({
  speaker: "ユーザー",
  text: "今日はとても嬉しいです",
  timestamp: new Date().toISOString(),
  audio: audioBase64,
  audio_format: "webm"
}));

// レスポンス受信
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "analysis_result") {
    console.log("感情スコア:", data.sentiment);
    console.log("音声特徴:", data.audio);

    // 最も強い感情を取得
    const emotions = data.sentiment;
    const dominant = Object.keys(emotions).reduce((a, b) =>
      emotions[a] > emotions[b] ? a : b
    );
    console.log(`最も強い感情: ${dominant} (${emotions[dominant].toFixed(2)})`);
  }
};

// Base64変換ヘルパー
function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}
```

---

## トラブルシューティング

### 感情分析関連

#### Q1: モデルのダウンロードに時間がかかる

**A:** 初回起動時は約500MBのモデルをダウンロードします。2回目以降はキャッシュから読み込まれるため高速です。

#### Q2: CPU推論が遅い

**A:** 以下を試してください：
- `torch.set_num_threads()`の値を調整（現在4）
- 短いテキストで分割処理
- バッチ処理の実装（将来的な改善）

#### Q3: 感情スコアが期待と異なる

**A:**
- モデルはWRIMEデータセットで学習されています
- 文脈によってスコアは変動します
- 複数の感情が混在する場合、各スコアは分散します

### 音声分析関連

#### Q4: WebMファイルが処理できない

**A:** FFmpegがインストールされているか確認：
```bash
ffmpeg -version
```

インストールされていない場合：
```bash
brew install ffmpeg  # macOS
apt-get install ffmpeg  # Ubuntu
```

#### Q5: ピッチが0.0になる

**A:** 以下の原因が考えられます：
- 音声が無音または非常に小さい
- ノイズが多すぎる
- 音声の長さが短すぎる（1秒未満）

#### Q6: 音量が常に低い

**A:**
- 入力音声のゲインを確認
- マイクの設定を確認
- 正規化係数（現在3.0）を調整可能

### 一般的な問題

#### Q7: メモリ不足エラー

**A:**
- 感情分析モデル: 約500MB必要
- 長い音声ファイル: 追加で100〜200MB
- システムメモリ: 最低2GB推奨

#### Q8: ImportError: No module named 'xxx'

**A:** 依存関係を再インストール：
```bash
uv add torch transformers librosa numpy soundfile pydub
```

#### Q9: 起動時にエラーが出る

**A:** ログを確認：
```bash
mise run start:backend
```

エラーメッセージに応じて対処：
- `ModuleNotFoundError` → 依存関係のインストール
- `RuntimeError` → モデルのダウンロード確認
- `ValueError` → 設定ファイルの確認

---

## パフォーマンスチューニング

### CPU推論の最適化

```python
# sentiment.py内で調整可能
torch.set_num_threads(4)  # CPUコア数に応じて調整
```

### モデルキャッシュの場所

デフォルトでは `~/.cache/huggingface/` にキャッシュされます。

環境変数で変更可能：
```bash
export HF_HOME=/path/to/cache
```

### 推奨システム要件

| 項目 | 最小 | 推奨 |
|------|------|------|
| CPU | 2コア | 4コア以上 |
| メモリ | 2GB | 4GB以上 |
| ディスク空き容量 | 1GB | 2GB以上 |

---

## 今後の拡張予定

- [ ] GPU対応
- [ ] バッチ処理の実装
- [ ] モデルの量子化（CPU高速化）
- [ ] リアルタイムストリーミング音声処理
- [ ] 感情履歴のトレンド分析
- [ ] 複数話者の感情比較

---

## 参考リンク

- [WRIME Dataset](https://github.com/ids-cv/wrime)
- [neuralnaut/deberta-wrime-emotions](https://huggingface.co/neuralnaut/deberta-wrime-emotions)
- [Librosa Documentation](https://librosa.org/doc/latest/index.html)
- [Transformers Documentation](https://huggingface.co/docs/transformers/)

---

## サポート

問題が発生した場合は、以下の情報を含めて報告してください：

1. エラーメッセージの全文
2. 使用しているPythonバージョン
3. OS情報
4. 実行したコマンド
5. 入力データのサンプル（可能な範囲で）
