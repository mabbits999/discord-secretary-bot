# Discord 秘書AIボット

Discord 内で次のことができる、常時稼働向けの秘書AIボットです。

## できること

・/ask で秘書AIに質問
・/research で調べ物を依頼
・/knowledge で knowledge フォルダの資料から答える
・/delegate でワーカーに依頼を送る
・/calendar_add で Google カレンダーに予定を追加
・/remind でチャンネルに時刻指定リマインド

## フォルダ構成

```text
discord_secretary_bot/
  app/
    bot.py
    calendar_service.py
    config.py
    db.py
    knowledge.py
    llm.py
  knowledge/
    sample.txt
  Dockerfile
  main.py
  README.md
  render.yaml
  requirements.txt
```

## 1. Discord 側の準備

### アプリ作成
1. Discord Developer Portal を開く
2. New Application を押す
3. Bot を追加する
4. Token を発行する
5. OAuth2 で bot と applications.commands を選ぶ
6. 権限は最低でも Send Messages / Use Application Commands / Read Message History を付ける
7. 発行された招待URLで自分のサーバーに入れる

## 2. Google カレンダー準備

1. Google Cloud でサービスアカウントを作る
2. Google Calendar API を有効化する
3. JSON キーを発行する
4. 使いたい Google カレンダーをそのサービスアカウントのメールアドレスに共有する
5. カレンダーIDを控える

## 3. 環境変数

最低限必要なもの

```env
DISCORD_BOT_TOKEN=xxxxxxxx
DISCORD_GUILD_ID=123456789012345678
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxx
MODEL_NAME=gpt-4.1-mini
TZ=Asia/Tokyo
DB_PATH=/var/data/bot.db
KNOWLEDGE_DIR=/var/data/knowledge
GOOGLE_CALENDAR_ID=primary_or_calendar_id
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account", ...}
```

Claude 系を使うなら

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxx
MODEL_NAME=claude-3-7-sonnet-latest
```

## 4. ローカル起動

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## 5. Render にデプロイ

### いちばん簡単な方法
1. このフォルダを GitHub に push
2. Render で New > Blueprint を選ぶ
3. リポジトリをつなぐ
4. `render.yaml` を読ませる
5. Environment Variables に上の環境変数を入れる
6. Deploy を押す

### Render で保存を残すとき
DB_PATH と KNOWLEDGE_DIR は永続ディスク上のパスを使うと便利です。
例

```env
DB_PATH=/var/data/bot.db
KNOWLEDGE_DIR=/var/data/knowledge
```

## 6. コマンド例

### /ask
```text
/ask question: 今週やるべき優先タスクを3つに絞って
```

### /research
```text
/research topic: AI動画編集の最新トレンド
```

### /knowledge
```text
/knowledge question: UTAGEのセミナー前日リマインド配信の流れを教えて
```

### /delegate
```text
/delegate worker:@山田 title:動画編集依頼 due_date:2026-04-10 description:素材URLは◯◯、冒頭3秒を強く
```

### /calendar_add
```text
/calendar_add title:おさる講座 Day1 start:2026-04-10T21:00 end:2026-04-10T22:30 description:Zoomあり
```

### /remind
```text
/remind remind_at:2026-04-10 20:00 title:講座開始1時間前 body:ZoomURLとスライドを最終確認してください
```

## 7. knowledge の使い方

`knowledge/` に `.txt` や `.md` を入れてください。
このボットは、その中から近い内容を探して答えます。

おすすめ

・UTAGE手順
・LINE配信テンプレ
・案件管理ルール
・講座スケジュール
・よくある質問

## 8. 次に足すと強い機能

・Googleスプレッドシート自動記録
・Notion検索
・フォーム入力から自動依頼
・音声文字起こし
・投稿文自動作成
・月末の請求リマインド
・担当者の自動振り分け

## 9. 注意

・`GOOGLE_SERVICE_ACCOUNT_JSON` は 1 行の JSON にして環境変数へ入れる
・コマンドが出ないときは `DISCORD_GUILD_ID` を入れて再デプロイすると反映が早い
・初回は bot に十分な権限を付ける
