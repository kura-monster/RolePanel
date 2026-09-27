# RolePanel Bot

Discord用のロールパネルBot。ボタンをクリックするだけでロールを自由に切り替えられます。

## 機能

- **スラッシュコマンド対応** — モダンなDiscord UIで操作
- **ボタン式ロール選択** — ユーザーはボタンをクリックするだけ
- **管理者限定** — パネルの作成・編集・削除は管理者権限が必要
- **永続化** — Bot再起動後もパネルのボタンが機能
- **複数パネル対応** — サーバー内に複数のパネルを設置可能

## セットアップ

### 1. Botの作成

1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリケーションを作成
2. Bot設定で **SERVER MEMBERS INTENT** を有効化
3. OAuth2 → URL Generator で `bot` + `applications.commands` スコープ、`Administrator` 権限を選択
4. 生成されたURLでサーバーに招待

### 2. インストール

```bash
pip install -r requirements.txt
```

### 3. 設定

```bash
cp .env.example .env
```

`.env` ファイルにBotのトークンを設定:

```
DISCORD_TOKEN=your_bot_token_here
```

### 4. 起動

```bash
python bot.py
```

## コマンド一覧

| コマンド | 説明 |
|---|---|
| `/rolepanel create` | 新しいロールパネルを作成 |
| `/rolepanel add` | パネルにロールを追加 |
| `/rolepanel remove` | パネルからロールを削除 |
| `/rolepanel edit` | パネルのタイトル・説明・色を変更 |
| `/rolepanel delete` | パネルを削除 |
| `/rolepanel list` | パネル一覧を表示 |
| `/rolepanel refresh` | パネルを再送信 |

## 使い方の例

```
1. /rolepanel create title:ロール選択 description:好きなロールを選んでください color:青
2. /rolepanel add panel_id:1 role:@ゲーマー emoji:🎮
3. /rolepanel add panel_id:1 role:@アーティスト emoji:🎨
```

ユーザーはパネルのボタンをクリックするだけでロールを付与/剥奪できます。
