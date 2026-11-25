# モデルカード

[README に戻る](../README.md)

## v0.1.1

| 項目 | 内容 |
| --- | --- |
| モデル | 95 token Transformer + AdaLN、最大8局面の履歴 |
| 入力条件 | 自他のレーティング、残り持ち時間 |
| 出力 | 合法手の着手確率 |
| 推論重み | float32、14,723,681パラメータ（58,922,020 bytes） |
| 初期重み | 事前学習済みの将棋Transformer EMA |
| 学習データ | 将棋倶楽部24、約19億局面、自然頻度 |
| 重みの選択 | 固定validation NLLが最良のEMA |

## 学習設定

- 評価用対局と同一着手列の重複を学習から除き、各着手を等重みで学習。R・時計の欠損は既知性maskで扱います。
- **条件dropout**: 両方使用70% / Rのみ10% / 時計のみ10% / 両方省略10%。
- **履歴短縮**: 8局面50% / 現在局面のみ25% / 2〜7局面を各1/24。

## 配布

[GitHub Releasesのv0.1.1](https://github.com/nyoki-mtl/shogi-human-policy/releases/tag/v0.1.1)で、`manifest.json`と`policy.safetensors`を配布しています。
ソースコードは[MIT License](../LICENSE)です。
