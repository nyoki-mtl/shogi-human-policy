# 入力仕様・API・配布形式

[README に戻る](../README.md)

## 局面と履歴

### SFEN と USI 着手列

```python
from shogi_human_policy import Position

position = Position()  # 平手初期局面
position = Position.from_sfen(sfen)
position = Position.from_sfen(sfen, moves=["7g7f", "3c3d"])
position = Position.from_usi("startpos moves 7g7f 3c3d")
position = Position.from_usi(sfen + " moves 7g7f 3c3d")
```

- `from_sfen` には盤面・手番・持ち駒・手数の 4 フィールドを渡します。
- `from_usi` は先頭の `position` や `sfen` の有無を問わず受け付けます。
- 着手列は USI 形式で、開始局面から進める順番に指定します。

### 棋譜ファイルと `ply`

```python
position = Position.from_file("game.kif", ply=30)
position = Position.from_file("game.kifu")
position = Position.from_kif(kif_text, ply=30)
```

- **対応形式**: KIF / KIFU / KI2 / CSA（`rsshogi` を使用）、および 1 局面分の `.sfen` / `.usi` テキスト。
- **文字コード**: UTF-8（BOM あり含む）を先に試し、失敗した場合は CP932（Shift-JIS）を使用します。`encoding="utf-16"` などで明示指定も可能です。
- **`ply` の意味**: 入力の開始局面から進める着手数です（`0` で開始局面、`None` または省略で末尾、`30` なら 30 手指した後の局面で 31 手目を予測）。SFEN 内の絶対手数とは区別します（`position.at_ply(30)` でも同様の切り出しが可能）。
- **分岐と終局記号**: 変化を含む棋譜は本譜のみを使用します。投了などの終局記号は着手数に含めず、末尾指定時は終局記号の直前の盤面になります。
- **ヘッダ情報**: 棋譜ヘッダの名前・R・持ち時間から推論条件を自動設定することはありません。

### 履歴の扱いと手番視点の正規化

- 棋譜や着手列を渡すと、途中局面でもそれまでの履歴を保持します。
- 推論には現在局面と最大 7 手前まで（計最大 8 局面）を使用します。不足分はパディング（盤面 0、持ち駒符号化値 31）で埋めます。SFEN 単体からは過去の履歴や千日手反復を復元できません。
- 入力は現在の手番側から見た向きに統一します（後手番では盤面を 180 度回転して駒色を反転し、持ち駒の自他を入れ替えます）。
- `history_plies=0` で現在局面のみ、既定の `7` で最大 8 局面を使用します（短縮時は残した履歴内で反復回数を再計算します）。
- `position.to_usi()` で履歴付き USI 文字列、`position.to_sfen()` で現在局面の SFEN、`position.to_board()` で独立した `rsshogi` 盤面を取得できます。

---

## CLI

```console
shogi-human-policy predict --model models/v0.1.1 --position "startpos" --moves 7g7f 3c3d
shogi-human-policy predict --model models/v0.1.1 --file game.kif --ply 30 --format json
```

- `--position` と `--file` は排他指定です（両方省略時は平手初期局面）。
- `--moves` は `--position` に着手を追加し、`--ply` はその後に適用します（`--file` とは併用不可）。
- `--encoding` は `--file` 入力時に使用します。

---

## レーティングと時計（`Conditions`）

| 引数 | 順序と意味 | 不明時 |
|---|---|---|
| `Conditions.ratings` | `(手番側R, 相手R)` | `None` |
| `Conditions.clocks` | `(手番側の利用可能秒数, 相手の利用可能秒数)` | `None` |

- 値はすべて有限な非負の数を指定します。片方のみ不明な場合はその組全体を `None` にしてください。
- **レーティング**: 学習元の将棋倶楽部24の尺度を想定しています（他サービスへの換算は未検証）。駒落ちで指定する場合は黒を下手、白を上手として扱います。
- **時計（着手前の利用可能秒数）**: 当該手に実際に消費した時間は含めません。
  - 秒読みあり: `残り本時間 + その手で使える秒読み`
  - 切れ負け: `残り本時間`
  - フィッシャー: `現在の残り時間`（着手後の加算は含めない）
  - 相手側も現在観測している時計状態をそのまま渡します（ミリ秒は秒へ変換）。
- **内部正規化**: R は `(R - 1500) / 1500`、時計は `log1p(秒数) / log1p(3600)` に変換し、不明な組は 0 置換＋既知性 mask で区別します（`0秒` を不明扱いすることはありません）。

---

## 出力とバッチ推論

- **`Prediction.moves`**: 確率降順に並んだ合法手リスト。`probability` は全合法手に対する確率（表示用に上位件数で切っても再正規化しません）、`label` は 1496 次元の内部ラベルです。
- **`result.as_rows(position)`**: `usi` / `notation`（日本語表記） / `probability` の辞書列を返します。`position` には推論時と同じ局面を渡してください。
- **`entropy` / `legal_count`**: 全合法手分布の自然対数エントロピーと合法手数（合法手がない局面では空リストと `entropy=0`）。
- **`temperature`**: 既定は `1`（正の有限値を指定可能）。評価時は必ず `1` を使用します。
- **バッチ推論**: `predict_batch(positions, conditions=None)` で複数局面を一括処理できます（`conditions` は局面数と同じ長さの列）。
- **スレッド数**: CLI はスレッド数を既定 `4` に設定し、Python API は呼び出し元の設定を維持します。
- 本ライブラリは着手分布の予測のみを行い、探索・投了判断・時間配分を行う USI エンジン機能は含みません。

---

## 配布形式

1 モデルを `manifest.json` と `policy.safetensors` の 2 ファイルで構成します（学習時の optimizer・EMA 状態・未学習の value 系 head は含めません）。

- **`manifest.json`**: schema `shogi-human-policy-v1`、モデルバージョン、モデル構造、EMA 選択、1496 ラベル、8 履歴、入力正規化・パディング仕様、geometry と重みの SHA-256 を記録します。`v0.1.1` の manifest は [model-manifest.json](model-manifest.json) を参照してください。
- **検証**: 読み込み時に SHA-256、全パラメータ名、shape、有限性、同梱 `geometry.npz` との整合性を検査します（`safetensors` 形式のみを使用）。
- 重みファイルと棋譜データは Git に含めません。
