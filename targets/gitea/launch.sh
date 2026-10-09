#!/bin/sh
# 起一个本地 Gitea 实例——这条场景的被测产品，一个真实的开源应用。
#
#   targets/gitea/launch.sh                    # http://localhost:3100
#   GITEA_PORT=3101 targets/gitea/launch.sh    # 换端口
#   GITEA_VERSION=1.27.3 targets/gitea/launch.sh
#
# 单文件二进制 + SQLite，不依赖 Docker、不需要外网出口（下载那一次除外）。
# 二进制、数据库、仓库全在 .run/ 下，`rm -rf targets/gitea/.run` 就是一台全新实例。
set -e

HERE=$(cd "$(dirname "$0")" && pwd)
RUN="$HERE/.run"
BIN="$RUN/gitea"
CONF="$RUN/custom/conf/app.ini"
VERSION="${GITEA_VERSION:-1.27.3}"
PORT="${GITEA_PORT:-3100}"
BASE="http://localhost:$PORT/"
# 常驻管理员。存在的理由见下面建号那段注释——它是让清理永远管用的前提。
ADMIN_USER="${GITEA_ADMIN_USER:-rb-admin}"
ADMIN_PASS="${GITEA_ADMIN_PASS:-Roadbook-Admin-123}"
ADMIN_MAIL="${GITEA_ADMIN_MAIL:-rb-admin@example.com}"

case "$(uname -s)" in
  Darwin) PLATFORM="darwin-10.12" ;;
  Linux)  PLATFORM="linux" ;;
  *) echo "没为 $(uname -s) 准备二进制；去 https://dl.gitea.com/gitea/ 自己下，放到 $BIN" >&2; exit 1 ;;
esac
case "$(uname -m)" in
  arm64|aarch64) ARCH="arm64" ;;
  x86_64|amd64)  ARCH="amd64" ;;
  *) echo "没为 $(uname -m) 准备二进制" >&2; exit 1 ;;
esac

mkdir -p "$RUN"

if [ ! -x "$BIN" ]; then
  URL="https://dl.gitea.com/gitea/$VERSION/gitea-$VERSION-$PLATFORM-$ARCH"
  echo "下载 Gitea $VERSION（$PLATFORM-$ARCH）…"
  curl -fSL --progress-bar -o "$BIN.part" "$URL"
  echo "校验 SHA256…"
  curl -fSL -o "$BIN.sha256" "$URL.sha256"
  if command -v shasum >/dev/null 2>&1; then
    ACTUAL=$(shasum -a 256 "$BIN.part" | awk '{print $1}')
  else
    ACTUAL=$(sha256sum "$BIN.part" | awk '{print $1}')
  fi
  EXPECTED=$(awk '{print $1}' "$BIN.sha256")
  [ "$ACTUAL" = "$EXPECTED" ] || { echo "SHA256 对不上：期望 $EXPECTED，实得 $ACTUAL" >&2; exit 1; }
  rm -f "$BIN.sha256"
  mv "$BIN.part" "$BIN"
  chmod +x "$BIN"
fi

if [ ! -f "$CONF" ]; then
  echo "生成 $CONF…"
  mkdir -p "$(dirname "$CONF")"
  SECRET_KEY=$("$BIN" generate secret SECRET_KEY)
  INTERNAL_TOKEN=$("$BIN" generate secret INTERNAL_TOKEN)
  JWT_SECRET=$("$BIN" generate secret JWT_SECRET)
  cat > "$CONF" <<EOF
APP_NAME = Roadbook OSS Target (Gitea)
RUN_USER = $(id -un)
RUN_MODE = prod
WORK_PATH = $RUN

[server]
PROTOCOL = http
HTTP_ADDR = 127.0.0.1
HTTP_PORT = $PORT
ROOT_URL = $BASE
DISABLE_SSH = true
START_SSH_SERVER = false
OFFLINE_MODE = true
LANDING_PAGE = home

[database]
DB_TYPE = sqlite3
PATH = $RUN/data/gitea.db

[repository]
ROOT = $RUN/data/repositories

[security]
INSTALL_LOCK = true
SECRET_KEY = $SECRET_KEY
INTERNAL_TOKEN = $INTERNAL_TOKEN
PASSWORD_HASH_ALGO = pbkdf2

[oauth2]
JWT_SECRET = $JWT_SECRET

; 自动化要在一个干净实例上注册新用户，所以关掉邮箱确认和图形验证码。
; 这不是"为了好测而放松标准"——它们是真实产品里的可选项，只是本场景不验它们。
[service]
DISABLE_REGISTRATION = false
ENABLE_CAPTCHA = false
REGISTER_EMAIL_CONFIRM = false
ENABLE_NOTIFY_MAIL = false
DEFAULT_KEEP_EMAIL_PRIVATE = true

[openid]
ENABLE_OPENID_SIGNIN = false
ENABLE_OPENID_SIGNUP = false

[mailer]
ENABLED = false

[cron]
ENABLED = false

[log]
MODE = console
LEVEL = Warn
EOF
fi

# 空实例上注册的第一个账号会自动成为管理员，而 Gitea **不允许删掉最后一个管理员**——
# 于是场景跑出来的那个用户永远清理不掉，cleanup.sh 时灵时不灵。先钉一个常驻管理员垫底，
# 场景注册的就永远是可删的普通用户。它只用来占位，场景不登录它。
#
# 表还没建出来时 admin 子命令会报 "no such table: user"，所以先单独跑一次 migrate。
"$BIN" migrate --config "$CONF" >/dev/null
if ! "$BIN" admin user list --config "$CONF" 2>/dev/null | awk 'NR > 1 && NF { found = 1 } END { exit !found }'; then
  echo "建常驻管理员 $ADMIN_USER（让场景用户始终是可删的普通用户）…"
  "$BIN" admin user create --config "$CONF" \
    --username "$ADMIN_USER" --password "$ADMIN_PASS" --email "$ADMIN_MAIL" \
    --admin --must-change-password=false >/dev/null
fi

echo "Gitea 起在 $BASE（数据在 $RUN）"
exec "$BIN" web --config "$CONF"
