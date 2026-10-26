#!/usr/bin/env bash
# ============================================================
# 代码冒险者 · Ubuntu 一键部署脚本（22.04 / 24.04 实测可用）
#
# 在**服务器**上、项目目录内执行：
#   sudo bash deploy/deploy.sh hongchi.xyz --https   # 域名 + 自动申请证书
#   sudo bash deploy/deploy.sh hongchi.xyz           # 先用 http 跑通
#   sudo bash deploy/deploy.sh 1.2.3.4               # 没有域名、只用公网 IP
#
# 脚本做的事：装依赖 → 建专用系统用户 → 部署代码 → 建库建账号 →
# 生成生产 .env（随机密钥、关闭直通登录）→ 构建前端 → 装 systemd + Nginx
# →（可选）申请 Let's Encrypt 证书并开启自动续期。
#
# 幂等：重复执行会保留已有的 .env 与数据库，只更新代码与配置。
# ============================================================
set -euo pipefail

SITE_NAME=""
ENABLE_HTTPS=0
for arg in "$@"; do
  case "$arg" in
    --https) ENABLE_HTTPS=1 ;;
    -*) echo "未知参数: $arg（可用：--https）"; exit 1 ;;
    *)
      case "$arg" in
        https://*) ENABLE_HTTPS=1 ;;
      esac
      SITE_NAME="$arg"
      ;;
  esac
done
SITE_NAME="${SITE_NAME#http://}"; SITE_NAME="${SITE_NAME#https://}"; SITE_NAME="${SITE_NAME%%/*}"

if [[ -z "$SITE_NAME" ]]; then
  echo "用法: sudo bash deploy/deploy.sh <域名或公网IP> [--https]"
  exit 1
fi
if [[ $EUID -ne 0 ]]; then
  echo "请用 root 或 sudo 执行"
  exit 1
fi

APP_USER="ca"
APP_DIR="/opt/code-adventurer"
WEB_DIR="/var/www/code-adventurer"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_NAME="code_adventurer"
DB_USER="ca_app"
PY_BIN="python3"

log() { echo -e "\n\033[1;36m==> $*\033[0m"; }

# ---------- 0. 判断是域名还是 IP ----------
# 域名要走 server_name + 可选的证书流程；IP 则只能 http、且没有 www。
IS_DOMAIN=1
if [[ "$SITE_NAME" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]]; then
  IS_DOMAIN=0
fi
SERVER_NAMES="$SITE_NAME"
WWW_OK=0
# 有人习惯直接输 www.xxx，统一收敛到裸域，否则会去找 www.www.xxx
if [[ "$SITE_NAME" == www.* ]]; then
  SITE_NAME="${SITE_NAME#www.}"
  SERVER_NAMES="$SITE_NAME www.$SITE_NAME"
  WWW_OK=1
fi
if [[ $IS_DOMAIN -eq 1 && $WWW_OK -eq 0 ]]; then
  # 只有 www 也能解析到本机时才把它写进 server_name / 证书，否则 certbot 会因
  # 「www 解析不到」直接失败（这是最容易踩的一步，所以提前查而不是交给 certbot 报错）
  WWW_IP="$(getent hosts "www.$SITE_NAME" | awk '{print $1}' | head -1 || true)"
  if [[ -n "$WWW_IP" ]]; then
    SERVER_NAMES="$SITE_NAME www.$SITE_NAME"
    WWW_OK=1
  fi
fi

# ---------- 0.5 DNS 预检 ----------
# 域名解析没生效时，Nginx 能起来但打开是「不是私密连接」或别人的页面，
# 证书申请也必然失败。提前查一次并给出确切提示，省得装完才排查。
if [[ $IS_DOMAIN -eq 1 ]]; then
  PUB_IP="$(curl -fsS --max-time 8 http://100.100.100.200/latest/meta-data/eipv4 2>/dev/null \
            || curl -fsS --max-time 8 https://ipinfo.io/ip 2>/dev/null || true)"
  DNS_IP="$(getent ahostsv4 "$SITE_NAME" 2>/dev/null | awk 'NR==1{print $1}' || true)"
  echo "本机公网 IP : ${PUB_IP:-未知}"
  echo "$SITE_NAME 解析到: ${DNS_IP:-未解析}"
  if [[ -n "$PUB_IP" && -n "$DNS_IP" && "$PUB_IP" != "$DNS_IP" ]]; then
    echo "⚠️ 域名没有指向本机：请在域名解析处把 A 记录改成 $PUB_IP，等 TTL 生效后重跑。"
    echo "   继续执行也能装好站点，但用域名访问会打不开。"
  elif [[ -z "$DNS_IP" ]]; then
    echo "⚠️ 域名暂无 A 记录：先去加一条 A 记录指向 $PUB_IP（主机记录填 @，需要 www 就再加一条）。"
  fi
fi

# ---------- 1. 系统依赖 ----------
log "安装系统依赖"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-dev build-essential \
  pkg-config default-libmysqlclient-dev nginx mysql-server rsync curl ca-certificates \
  >/dev/null

# Node 18+ 才能跑 Vite 6；Ubuntu 自带版本太旧，用 NodeSource 装 20.x
if ! command -v node >/dev/null 2>&1 || [[ "$(node -v | sed 's/v\([0-9]*\).*/\1/')" -lt 18 ]]; then
  log "安装 Node.js 20"
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >/dev/null
  apt-get install -y -qq nodejs >/dev/null
fi

# ---------- 1.5 Swap（2G 内存机器的保命配置）----------
# 本项目常驻内存大约是：MySQL 8 ~400MB + uvicorn(pandas/numpy 已加载) ~400MB
# + Nginx + 系统，2GiB 机器几乎没余量。学生跑一段 numpy 代码就可能触发 OOM
# killer 把后端杀掉，表现成"网站突然打不开"（journalctl 里能看到 Killed）。
# 加 2GB swap 兜住峰值，代价只是偶尔一处慢一点。
log "配置 swap"
if ! swapon --show 2>/dev/null | grep -q '/swapfile'; then
  if [[ ! -f /swapfile ]]; then
    fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=2048 status=none
    chmod 600 /swapfile
    mkswap /swapfile >/dev/null
  fi
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo "已启用 2GB swap"
else
  echo "swap 已存在，跳过"
fi

MEM_MB="$(free -m | awk '/^Mem:/{print $2}')"
if [[ "${MEM_MB:-0}" -lt 1900 ]]; then
  echo "⚠️ 检测到内存仅 ${MEM_MB}MB：已靠 swap 兜底，但如果访客多仍可能变慢。"
  echo "   建议升级到 2vCPU 4GiB，或把 CODE_RUN_ENABLED 设为 false 降低内存峰值。"
fi

# ---------- 1.6 停掉预装 Docker ----------
# 阿里云「应用镜像」下拉里常常只有 宝塔/WordPress/Docker/LNMP 可选，没有纯系统。
# Docker 是这四个里唯一不会和本脚本抢 80/3306 的，但 dockerd + containerd
# 常驻要吃掉 100~150MB，对本项目毫无用处（全是裸进程，不用容器）。
if systemctl list-unit-files 2>/dev/null | grep -q '^docker\.service'; then
  log "检测到预装 Docker，停止并禁用（本项目不用容器，省内存）"
  systemctl disable --now docker docker.socket containerd 2>/dev/null || true
  echo "已关闭 Docker；将来要用可执行 systemctl enable --now docker 恢复"
fi
# 顺带拦一下更危险的预装：宝塔/LNMP 会和脚本装的 Nginx、MySQL 直接打架
if [[ -f /etc/init.d/bt ]] || command -v bt >/dev/null 2>&1; then
  echo "⚠️ 检测到宝塔面板：它会占用 8888 并自装 Nginx/MySQL，与本次部署冲突。"
  echo "   建议重装系统并选择「Docker」或纯净镜像，否则请先手动卸载宝塔。"
fi

# ---------- 2. 专用系统用户 ----------
log "创建运行用户 $APP_USER"
if ! id -u "$APP_USER" >/dev/null 2>&1; then
  useradd --system --create-home --shell /usr/sbin/nologin "$APP_USER"
fi

# ---------- 3. 部署代码 ----------
log "同步代码到 $APP_DIR"
mkdir -p "$APP_DIR" "$WEB_DIR"
rsync -a --delete \
  --exclude '.git' --exclude 'node_modules' --exclude 'venv' --exclude '.venv' \
  --exclude '__pycache__' --exclude 'dist' --exclude '.env' --exclude '.env.production' \
  "$SRC_DIR"/ "$APP_DIR"/
mkdir -p "$APP_DIR/frontend" "$APP_DIR/backend"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# ---------- 4. Python 环境 ----------
log "创建虚拟环境并安装后端依赖"
if [[ ! -x "$APP_DIR/venv/bin/python" ]]; then
  "$PY_BIN" -m venv "$APP_DIR/venv"
fi
"$APP_DIR/venv/bin/pip" install -q --upgrade pip
"$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/backend/requirements.txt" \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
chown -R "$APP_USER:$APP_USER" "$APP_DIR/venv"

# ---------- 5. 数据库 ----------
log "配置 MySQL 数据库"
systemctl enable --now mysql >/dev/null 2>&1 || true

# 首次部署生成随机密码；重复部署沿用 .env 里已有的，避免把现有连接打断
ENV_FILE="$APP_DIR/backend/.env"
if [[ -f "$ENV_FILE" ]] && grep -q '^DB_URL=' "$ENV_FILE"; then
  DB_PASS="$(grep '^DB_URL=' "$ENV_FILE" | sed -E 's#.*ca_app:([^@]*)@.*#\1#')"
  echo "检测到已有 .env，沿用原数据库密码"
else
  DB_PASS="$(openssl rand -hex 16)"
fi

mysql --protocol=socket -uroot <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'127.0.0.1' IDENTIFIED BY '${DB_PASS}';
ALTER USER '${DB_USER}'@'127.0.0.1' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL

# ---------- 6. 生产 .env ----------
log "写入生产配置 backend/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  SECRET="$(openssl rand -hex 32)"
  cat > "$ENV_FILE" <<ENVEOF
# ===== 生产环境配置（由 deploy.sh 生成，含密钥，切勿提交到 Git）=====
ENV=prod

DB_URL=mysql+pymysql://${DB_USER}:${DB_PASS}@127.0.0.1:3306/${DB_NAME}?charset=utf8mb4
REDIS_URL=redis://127.0.0.1:6379/0

SECRET_KEY=${SECRET}
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 公网必须只允许本站域名访问（前后端同源部署，CORS 实际不生效，
# 但保留白名单能让「有人在别的页面里偷偷调你接口」多一层拦阻）
CORS_ORIGINS=http://${SITE_NAME}$([[ $IS_DOMAIN -eq 1 ]] && echo ",http://www.${SITE_NAME},https://${SITE_NAME},https://www.${SITE_NAME}" || echo "")

# 公网必须关闭直通登录，否则所有人共享同一账号
ALLOW_GUEST_LOGIN=false

# ===== AI（留空 = 离线演示模式，不花钱）=====
AI_BASE_URL=
AI_API_KEY=
AI_MODEL=
AI_TIMEOUT=30

# ===== 代码沙箱 =====
CODE_RUN_ENABLED=true
# 超时给到 10s（本地开发是 5s）：共享型实例（经济型 e）的 CPU 会被邻居抢占，
# 5 秒容易把学生本来正确的代码误判成"运行超时"，而这种误判极难想到是机器问题。
# 正常代码 0.1s 就跑完，放宽只是让死循环多等 5 秒。
CODE_RUN_TIMEOUT=10
CODE_RUN_PER_MINUTE=12
AI_CALL_PER_MINUTE=15
ENVEOF
  chmod 600 "$ENV_FILE"
  echo "已生成 .env（数据库密码和 JWT 密钥为随机值，已记录在本文件）"
else
  echo "已存在 .env，跳过（如需改 AI Key 请手动编辑 $ENV_FILE）"
  # 从 IP 换成域名、或先 http 后 https 时，白名单要跟着改，否则旧域名残留在里面
  NEW_CORS="http://${SITE_NAME}"
  if [[ $IS_DOMAIN -eq 1 ]]; then
    NEW_CORS="http://${SITE_NAME},http://www.${SITE_NAME},https://${SITE_NAME},https://www.${SITE_NAME}"
  fi
  if grep -q '^CORS_ORIGINS=' "$ENV_FILE"; then
    sed -i "s#^CORS_ORIGINS=.*#CORS_ORIGINS=${NEW_CORS}#" "$ENV_FILE"
    echo "已把 CORS_ORIGINS 更新为：${NEW_CORS}"
  fi
fi
chown "$APP_USER:$APP_USER" "$ENV_FILE"

# ---------- 7. 前端构建 ----------
log "构建前端"
cd "$APP_DIR/frontend"

# ICP 备案号：管局要求首页底部必须展示，抽查缺失会被要求整改。
# 用法：ICP_BEIAN="冀ICP备2026xxxxxx号-1" sudo bash deploy/deploy.sh hongchi.xyz --https
if [[ -n "${ICP_BEIAN:-}" ]]; then
  echo "VITE_ICP_BEIAN=${ICP_BEIAN}" > .env.production
  echo "已注入备案号：${ICP_BEIAN}（构建后显示在页面底部）"
elif [[ -f .env.production ]]; then
  echo "沿用已有 .env.production 里的备案号"
fi
if [[ -f package-lock.json ]]; then
  npm ci --registry=https://registry.npmmirror.com --silent
else
  npm install --registry=https://registry.npmmirror.com --silent
fi
# 服务器根路径托管，base 用默认的 '/'（GitHub Pages 那份才需要 --base=/liu-aochi/）
npm run build --silent
rsync -a --delete "$APP_DIR/frontend/dist/" "$WEB_DIR/dist/"
chown -R www-data:www-data "$WEB_DIR"

# ---------- 8. systemd 服务 ----------
log "安装 systemd 服务"
install -m 644 "$APP_DIR/deploy/code-adventurer.service" /etc/systemd/system/code-adventurer.service
systemctl daemon-reload
systemctl enable code-adventurer >/dev/null 2>&1 || true

# ---------- 9. Nginx ----------
log "配置 Nginx"
sed "s/__SERVER_NAME__/${SERVER_NAMES}/" \
  "$APP_DIR/deploy/nginx.conf" > /etc/nginx/sites-available/code-adventurer
ln -sf /etc/nginx/sites-available/code-adventurer /etc/nginx/sites-enabled/code-adventurer
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# ---------- 10. 防火墙 ----------
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  log "放行 80/443"
  ufw allow 80/tcp >/dev/null
  ufw allow 443/tcp >/dev/null
fi

# ---------- 11. 启动 ----------
log "启动后端服务"
systemctl restart code-adventurer
sleep 3

if systemctl is-active --quiet code-adventurer; then
  echo -e "\n\033[1;32m✅ 部署完成\033[0m"
else
  echo -e "\n\033[1;31m❌ 后端启动失败，查看日志：journalctl -u code-adventurer -n 50 --no-pager\033[0m"
fi

# ---------- 12. HTTPS（可选，域名才需要）----------
# 用 certbot 的 nginx 插件：它会自动改 server 块、加 443、把 80 重定向到 443，
# 比手写证书路径稳（续期时也会自动维护这份配置）。
HTTPS_ON=0
if [[ "$ENABLE_HTTPS" == "1" && $IS_DOMAIN -eq 1 ]]; then
  log "申请 HTTPS 证书"
  apt-get install -y -qq certbot python3-certbot-nginx >/dev/null

  CERT_ARGS=(-d "$SITE_NAME" --nginx --non-interactive --agree-tos --redirect
             -m "${CERT_EMAIL:-admin@$SITE_NAME}")
  if [[ $WWW_OK -eq 1 ]]; then
    CERT_ARGS+=(-d "www.$SITE_NAME")
  fi

  if certbot "${CERT_ARGS[@]}"; then
    HTTPS_ON=1
    systemctl enable --now certbot.timer >/dev/null 2>&1 || true
    echo "证书已签发，自动续期已交给 certbot.timer（每天检查，到期前 30 天续）"
  else
    echo "⚠️ 证书申请失败。最常见原因："
    echo "   1) 域名没解析到本机（先看上面的 DNS 预检结果）"
    echo "   2) 大陆服务器未备案，80 端口被运营商/云厂商拦截 —— 这种情况先解决备案"
    echo "   3) 80 端口被安全组挡住（阿里云「安全组」里要放行 80/443）"
    echo "   站点本身仍可通过 http 访问，处理好后重跑本脚本即可。"
  fi
elif [[ "$ENABLE_HTTPS" == "1" && $IS_DOMAIN -eq 0 ]]; then
  echo "⚠️ 用 IP 访问无法申请证书（Let's Encrypt 不给 IP 签发），已跳过 HTTPS。"
fi

if [[ $HTTPS_ON -eq 1 ]]; then ACCESS_URL="https://${SITE_NAME}"; else ACCESS_URL="http://${SITE_NAME}"; fi

cat <<SUMMARY

访问地址      ${ACCESS_URL}
健康检查      ${ACCESS_URL}/api/health
后端日志      journalctl -u code-adventurer -f
Nginx 日志    tail -f /var/log/nginx/code-adventurer.error.log
生产配置      ${APP_DIR}/backend/.env

首次使用请先注册账号（已关闭免登录直通）。
SUMMARY
if [[ $HTTPS_ON -eq 0 ]]; then
  if [[ $IS_DOMAIN -eq 1 ]]; then
    echo "如需 HTTPS：重跑 sudo bash deploy/deploy.sh ${SITE_NAME} --https"
  fi
fi
