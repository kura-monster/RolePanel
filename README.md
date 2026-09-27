# RolePanel Bot

Discord用のロールパネルBot。ボタンをクリックするだけでロールを自由に切り替えられます。

## 機能

- **プレフィックスコマンド (`!rp`)** — シンプルな操作
- **ボタン式ロール選択** — ユーザーはボタンをクリックするだけ
- **管理者限定** — パネルの作成・編集・削除は管理者権限が必要
- **永続化** — Bot再起動後もパネルのボタンが機能
- **複数パネル対応** — サーバー内に複数のパネルを設置可能

## セットアップ

### 1. Botの作成

1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリケーションを作成
2. Bot設定で **SERVER MEMBERS INTENT** と **MESSAGE CONTENT INTENT** を有効化
3. OAuth2 → URL Generator で `bot` スコープ、`Administrator` 権限を選択
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
| `!rp create <タイトル>` | 新しいロールパネルを作成 |
| `!rp add <ID> <ロール> [絵文字] [ラベル]` | パネルにロールを追加 |
| `!rp remove <ID> <ロール>` | パネルからロールを削除 |
| `!rp edit <ID> title <タイトル>` | タイトルを変更 |
| `!rp edit <ID> desc <説明>` | 説明文を変更 |
| `!rp edit <ID> color <色名>` | 色を変更 |
| `!rp delete <ID>` | パネルを削除 |
| `!rp list` | パネル一覧を表示 |
| `!rp refresh <ID>` | パネルを再送信 |

## 使い方の例

```
1. !rp create ロール選択
2. !rp add 1 @ゲーマー 🎮
3. !rp add 1 @アーティスト 🎨
4. !rp edit 1 desc 好きなロールを選んでください
5. !rp edit 1 color 青
```

ユーザーはパネルのボタンをクリックするだけでロールを付与/剥奪できます。
