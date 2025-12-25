"""
感情分析のテストスクリプト
様々な日本語テキストで感情分析を実行して結果を表示
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.analysis.sentiment import initialize_sentiment_model, analyze_sentiment


async def test_sentiment_analysis():
    """感情分析のテスト実行"""

    # モデル初期化
    print("=" * 60)
    print("感情分析モデルを初期化中...")
    print("=" * 60)
    await initialize_sentiment_model()
    print()

    # テストケース
    test_cases = [
        "今日のプレゼンは大成功でした！みんなに褒められて嬉しいです。",
        "プロジェクトが遅れていて本当に心配です。間に合うか不安です。",
        "あの人の態度は本当に許せない。腹が立って仕方がない。",
        "新しい技術を学ぶのが楽しみです。きっと成長できると思います。",
        "突然の発表にびっくりしました。予想外の展開です。",
        "このコードは信頼できそうです。しっかり設計されています。",
        "バグだらけで最悪のコードだ。見るのも嫌になる。",
        "明日の会議、うまくいくかな。ちょっと緊張します。",
        "チームメンバーを信じています。一緒なら乗り越えられます。",
        "失敗してしまった。みんなに迷惑をかけて申し訳ない気持ちです。",
    ]

    print("=" * 60)
    print("感情分析テスト結果")
    print("=" * 60)
    print()

    for i, text in enumerate(test_cases, 1):
        print(f"【テストケース {i}】")
        print(f"入力: {text}")
        print()

        # 感情分析実行
        result = await analyze_sentiment(text)

        # 結果を見やすく表示
        print("感情スコア:")
        emotions_sorted = sorted(result.items(), key=lambda x: x[1], reverse=True)

        for emotion, score in emotions_sorted:
            bar_length = int(score * 40)  # スコアを棒グラフで表示
            bar = "█" * bar_length
            print(f"  {emotion:6s} {score:.3f} {bar}")

        # 最も強い感情を表示
        dominant_emotion = emotions_sorted[0][0]
        dominant_score = emotions_sorted[0][1]
        print(f"\n  → 主要感情: {dominant_emotion} ({dominant_score:.1%})")
        print()
        print("-" * 60)
        print()


if __name__ == "__main__":
    asyncio.run(test_sentiment_analysis())
