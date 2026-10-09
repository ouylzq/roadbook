#!/bin/sh
# 清掉本地开源靶子（Gitea）跑出来的用户，连带 purge 掉他名下的仓库、工单和评论。
# Gitea 的界面上没有删用户的入口，这是唯一的路子。
#
#   scripts/cleanup_gitea_user.sh rb-20260930113000
#
# 放在 scripts/ 而不是 targets/gitea/ 是有原因的：runner 的脚本沙箱只放行
# 技能 scripts/ 下的脚本，清理这一步必须是 runner 能自己跑的——不然每跑一次就在
# 靶子上留一个用户，攒着攒着就没人清了。
set -e

ROOT=$(cd "$(dirname "$0")/.." && pwd)
RUN="$ROOT/targets/gitea/.run"
BIN="$RUN/gitea"
CONF="$RUN/custom/conf/app.ini"

if [ ! -x "$BIN" ] || [ ! -f "$CONF" ]; then
  echo "靶子还没起过（缺 $BIN 或 $CONF），没有可清理的东西" >&2
  exit 1
fi
if [ "$#" -eq 0 ]; then
  echo "用法: $0 <用户名> [<用户名> …]" >&2
  exit 2
fi

failed=0
for name in "$@"; do
  if "$BIN" admin user delete --config "$CONF" --username "$name" --purge >/dev/null 2>&1; then
    echo "已删除 $name"
  else
    echo "删不掉：$name" >&2
    failed=1
  fi
done
exit "$failed"
