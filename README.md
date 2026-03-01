# Simple Eagle (Fork)

> このリポジトリは [da2el-ai/simple-eagle](https://github.com/da2el-ai/simple-eagle) のフォークです。
> オリジナルに以下の機能を追加しています。

### フォークでの追加機能

- **パスワード認証** — 環境変数 `EAGLE_AUTH_PASSWORD` でパスワードを設定可能（未設定時は認証なし）
- **ダークモード / テーマ切替** — ライト・ダーク・システム連動の3モード
- **QRコード表示** — ログイン画面でサーバーURLのQRコードを表示し、スマホからの接続を簡単に
- **Lightbox 改善** — 詳細表示UIの改善
- **自動リロード** — Eagle ライブラリの変更を検知して自動で画像一覧を更新（タブ復帰時にも対応）
- **未分類フォルダ** — フォルダ未割り当てのアイテムを一覧表示

---

画像管理ソフトのEagleをスマホから見たくて作成したシンプルなインターフェースです。

<table>
  <tr>
    <td><img src="img/screen_1.png" width="200"></td>
    <td><img src="img/screen_2.png" width="200"></td>
    <td><img src="img/screen_3.png" width="200"></td>
  </tr>
</table>

## 機能概要

### できること

- フォルダツリーによるフォルダナビゲーション
- 未分類（フォルダ未割り当て）アイテムの表示
- 無限スクロールで全件表示
- 詳細表示（大きい画像はJPEG圧縮して表示）
- フィルタリング（星評価・拡張子・キーワード・タグ）
- ⭐️評価（単体・複数一括）
- 削除（単体・複数一括）
- ダークモード / テーマ切替
- 自動リロード（ポーリング＋タブ復帰時の変更検知）
- グリッドサイズ・表示モード（Cover / Contain）の切替

### できないこと

- ゴミ箱フォルダの閲覧（APIが存在しない）
- フォルダ移動（APIが存在しない）

## 必要環境

- Eagle
  - https://eagle.cool/
- Python
- Node.js（フロントエンドのビルドに必要）
- スマホ回線で見るにはVPNを設定する必要があります
  - 個人的にはTailscaleがおすすめです
  - https://tailscale.com/


## 更新履歴

- 2026.03.01
  - 自動リロード機能の変更検知を修正（最新アイテムID比較方式）
  - ヘッダーに自動リロード ON/OFF トグルボタンを追加
  - タブ復帰時の自動リロード対応
  - 未分類フォルダの表示対応
  - 無限スクロール改善・起動時の2重ロード修正
  - ビルド成果物（`dist/`）を git 管理外に変更
- 2025.06.16
  - フィルターに⭐️0（評価なし）を追加
  - バックエンドのzip圧縮を有効化してjsonの容量を削減
- 2025.06.08
  - 画像削除（ゴミ箱フォルダへの移動）
  - 複数指定削除
  - 複数指定⭐️評価
  - EagleAPIが貧弱すぎるのでこれ以上の機能追加はできないと思います
- 2025.06.07
  - 無限スクロール対応
  - フィルタリング機能追加
- 2025.05.30
  - ⭐️評価の変更機能を追加
  - 一覧画像の正方形トリミングする・しない切り替えボタンを追加
  - 一覧画像のサイズを保存するようにした



## インストール

EagleをインストールしているPCで実行してください。

```
git clone https://github.com/kai-rin/simple-eagle.git
cd simple-eagle
npm install
npm run build
```

> **Note:** `dist/` は git 管理外のため、クローン後にフロントエンドのビルドが必要です。

## 実行

あらかじめEagleを起動しておく必要があります。

### 認証パスワードの設定（任意）

`run.bat.example`（または `run.sh.example`）をコピーしてリネームし、パスワードを設定してください。

```
copy run.bat.example run.bat
```

`run.bat` 内の下記行のコメントを外してパスワードを設定します：
```
REM set EAGLE_AUTH_PASSWORD=your_password_here
↓
set EAGLE_AUTH_PASSWORD=任意のパスワード
```

未設定の場合は認証なしでアクセスできます。

### Windows で使う

```
cd simple-eagle
run.bat

〜必要なライブラリがインストールされる〜

INFO:     Application startup complete.
```

- `Application startup complete.` が表示されたら起動完了です
- `http://{起動しているPCのIPアドレス}:8000` にスマホからアクセス

### mac で使う

`run.sh.example` をコピーして `run.sh` を作成してください。

```
cd simple-eagle
cp run.sh.example run.sh

# 実行権限の付与が最初に一度だけ必要です
chmod 755 run.sh

./run.sh

〜必要なライブラリがインストールされる〜

INFO:     Application startup complete.
```

- `Application startup complete.` が表示されたら起動完了です
- `http://{起動しているPCのIPアドレス}:8000` にスマホからアクセス



## ライセンス

MIT
