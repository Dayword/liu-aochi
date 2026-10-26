#!/usr/bin/env bash
# ============================================================
# 本机打包：把「可以直接部署」的整套代码打成一个压缩包
#
# 为什么需要它：2C2G 的小云服务器上跑 `npm ci`，要写几万个小文件，
# 会把 40G ESSD Entry 云盘的吞吐打满（阿里云告警 SysDisBPS），连带拖住
# sshd —— 表现成「SSH 连上了但两分钟收不到密码提示」。而前端产物只有 2.3MB，
# 在本机构建好再传上去，服务器就完全不需要 Node。
#
# 用法（在项目根目录）：
#   bash scripts/pack.sh                 # 全套：会先 npm run build
#   bash scripts/pack.sh --no-build      # dist 已是最新，直接打包
#
# 产物：ca-deploy.tar.gz（默认放项目根目录）
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUT:-$ROOT/ca-deploy.tar.gz}"
DO_BUILD=1

for arg in "$@"; do
  case "$arg" in
    --no-build) DO_BUILD=0 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "未知参数: $arg（可用：--no-build）"; exit 1 ;;
  esac
done

cd "$ROOT"

if [[ $DO_BUILD -eq 1 ]]; then
  echo "==> 1/3 构建前端（约 30~60 秒）"
  cd "$ROOT/frontend"
  if [[ ! -d node_modules ]]; then
    npm ci --registry=https://registry.npmmirror.com
  fi
  npm run build
  cd "$ROOT"
else
  echo "==> 1/3 跳过构建（沿用现有 frontend/dist）"
fi

if [[ ! -f "$ROOT/frontend/dist/index.html" ]]; then
  echo "❌ frontend/dist/index.html 不存在，请先构建：cd frontend && npm run build"
  exit 1
fi
echo "    前端产物：$(du -sh frontend/dist | cut -f1) / $(find frontend/dist -type f | wc -l) 个文件"

echo "==> 2/3 打包"
# 先写到项目外的临时目录再挪过来：直接写进项目目录会让 tar 把自己正在读的
# 目录里的新文件也扫到，报 "file changed as we read it"（exit 1）并中断脚本。
# 在临时目录里 cd 之后只用**相对文件名**：Windows 版 GNU tar 会把 -f 的
# C:\... 路径当成远程主机（报 "Cannot connect to C: resolve failed"），
# 相对名可以完全绕开这个坑，也顺便兼容 macOS 的 bsdtar（它没有 --force-local）。
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
# 刻意排除：node_modules（体积大且服务器用不到）、.git（服务器不做版本管理）、
#           虚拟环境、字节码、以及所有 .env（里面有 AI Key 和数据库密码）
set +e
(
  cd "$TMP_DIR" || exit 2
  tar -czf pkg.tar.gz \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='.env.local' \
    --exclude='.env.production' \
    -C "$ROOT" .
)
TAR_RC=$?
set -e
# tar 在「读一个正在变化的目录」时会返回 1（file changed as we read it），
# 包内容本身是好的，只有 2 以上才是真失败。
if [[ $TAR_RC -gt 1 || ! -f "$TMP_DIR/pkg.tar.gz" ]]; then
  echo "❌ 打包失败（tar exit=${TAR_RC}）"
  exit 1
fi
mv -f "$TMP_DIR/pkg.tar.gz" "$OUT"

echo "==> 3/3 完成"
echo "    产物：$OUT"
echo "    大小：$(du -h "$OUT" | cut -f1)"
cat <<TIP

下一步（在你自己的电脑上执行，把 IP 换成你的）：

  scp "$OUT" root@39.96.223.77:/root/

然后 SSH 上去，一条命令装完：

  cd /root && mkdir -p liu-aochi && tar -xzf ca-deploy.tar.gz -C liu-aochi \\
    && cd liu-aochi && sudo bash deploy/deploy.sh 39.96.223.77 --skip-build

TIP
