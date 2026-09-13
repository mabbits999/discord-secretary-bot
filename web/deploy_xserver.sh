#!/usr/bin/env bash
# ページ総覧を Xserver (mashimashi.jp) にアップロードする。
#
# 使い方:
#   1. web/.deploy.env に FTP_HOST / FTP_USER / FTP_PASS を書く（.deploy.env.example 参照）
#   2. bash web/deploy_xserver.sh
#
# アップロード先は FTP_REMOTE_DIR（既定: /mashimashi.jp/public_html/hub）。
# サブドメイン hub.mashimashi.jp を Xserver で作れば同じフォルダが公開されます。
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
env_file="${DEPLOY_ENV:-$here/.deploy.env}"
# .deploy.env からは接続情報の3つだけ読む。FTP_REMOTE_DIR は他プロジェクトの
# .deploy.env を流用したときに別フォルダへ上書きしないよう、ファイルからは読まない。
read_env() { grep -E "^$1=" "$env_file" 2>/dev/null | tail -1 | cut -d= -f2- ; }
if [[ -f "$env_file" ]]; then
  FTP_HOST="${FTP_HOST:-$(read_env FTP_HOST)}"
  FTP_USER="${FTP_USER:-$(read_env FTP_USER)}"
  FTP_PASS="${FTP_PASS:-$(read_env FTP_PASS)}"
fi
: "${FTP_HOST:?FTP_HOST を .deploy.env に書いてください}"
: "${FTP_USER:?FTP_USER を .deploy.env に書いてください}"
: "${FTP_PASS:?FTP_PASS を .deploy.env に書いてください}"
remote_dir="${FTP_REMOTE_DIR:-/mashimashi.jp/public_html/hub}"
dry=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) dry="yes";;
    --remote-dir) remote_dir="$2"; shift;;
    *) echo "unknown option: $1" >&2; exit 2;;
  esac
  shift
done

case "$remote_dir" in
  */lp-skill|*/lp-skill/*) echo "lp-skill（会員サイト）には上書きしません: $remote_dir" >&2; exit 1;;
esac

python3 "$here/build.py"

echo "upload: $here/../public_html/hub/index.html -> ftp://$FTP_HOST$remote_dir/index.html"
if [[ -n "$dry" ]]; then echo "(dry-run: 送信しません)"; exit 0; fi

curl --ssl --ftp-create-dirs -sS --fail \
  --netrc-file <(printf 'machine %s login %s password %s\n' "$FTP_HOST" "$FTP_USER" "$FTP_PASS") \
  -T "$here/../public_html/hub/index.html" "ftp://$FTP_HOST$remote_dir/index.html"
echo "done: https://mashimashi.jp${remote_dir#/mashimashi.jp/public_html}/"
