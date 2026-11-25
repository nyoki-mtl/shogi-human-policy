# shogi-human-policy

- 利用者への説明と文書は日本語を既定とする。
- 推論API、入力エンコード、公開用モデル形式と性能資料を所有する。
- 学習、元DB、checkpoint運用は隣接trainerの所有物で、ここから変更しない。
- GitHub repository作成、push、release、モデル公開は明示的な依頼があるまで行わない。
- `models/`と`work_dir/`はローカル専用。学習state、棋譜DB、認証情報、個別対局IDをGitへ追加しない。
- 数値はsnapshot、評価集合、精度、合法手による正規化と分母を明記する。
- policy予測の一致率を棋力やレーティング校正の保証として扱わない。
- 利用者向け文書は仕様、操作手順、測定結果を簡潔に記載する。棋力保証に関する定型の注意書きや公開前の事情を追加しない。
- 変更後はfocused tests、Ruff、`git diff --check`を実行し、検証済みの変更だけを日本語でローカルcommitする。
