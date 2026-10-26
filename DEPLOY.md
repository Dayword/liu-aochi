# 公网部署指南（让人在局域网外也能访问）

> 目标读者：自己的电脑上跑得好好的，现在想让别人（面试官、同学、HR）直接打开链接就能用。

## 0. 先理解一个前提：GitHub Pages 只能放前端

目前 `https://dayword.github.io/liu-aochi/` 上跑的是**纯前端静态文件**，没有后端、没有数据库。
所以在线打开只能看到界面，登录、AI 对话、跑代码、闯关进度全部 404 —— 这不是 bug。

要让功能真的可用，**必须有一台 7×24 在公网的后端**。可选方案：

| 方案 | 你的电脑需要开机吗 | 成本 | 适合 |
|---|---|---|---|
| **云服务器**（推荐） | 不需要 | 学生机 ¥50~120/年 | 长期给别人用、放简历 |
| 内网穿透（cpolar/frp） | **需要，且要一直联网** | 免费有额度限制 | 临时演示 30 分钟 |
| Railway/Render 等托管 | 不需要 | 免费额度 | 但跑不了 Python 沙箱，MySQL 要换云库 |

**本指南走云服务器路线**：你的电脑只负责写代码和推 Git，服务和沙箱全在服务器上跑，
本机零负担。

### 服务器选型

- 配置：**2 核 2G 内存 / 40G 盘**起步。`numpy`+`pandas` 常驻约 300MB，沙箱单次最多 512MB。
- 系统：**Ubuntu 22.04 或 24.04 LTS**（脚本按这个写的）。
- 带宽：1~3M 够用（页面产物 gzip 后约 1MB，AI 对话是文本流）。
- 厂商：腾讯云轻量 / 阿里云 ECS 学生机都行，选离用户近的地域。
- **域名**：用 IP 访问可以跳过备案；想用域名 + HTTPS 则国内服务器需要 ICP 备案（约 1~2 周）。
  先跑起来建议直接用 IP，等稳定了再挂域名。

#### 下单时逐项怎么填（阿里云 ECS / 腾讯云 CVM 都适用）

| 选项 | 填什么 | 原因 |
|---|---|---|
| 地域 | 离你/用户最近的（华北用户选北京） | 延迟最低；**创建后不能改** |
| 实例规格 | 优先 **2vCPU 4GiB**；预算紧选 **2vCPU 2GiB 的「通用算力型 u1」** | 见下面的「别选共享型」 |
| 系统盘 | 40GiB ESSD Entry | 够用，代码+依赖约 3GB |
| 操作系统 | **Ubuntu 24.04 64位** | 与本脚本完全匹配 |
| 预装应用 | **「无」/ 纯净系统** | ⚠️ 千万别选宝塔：它会自装一套 Nginx+MySQL 占 8888 端口，和本脚本打架 |
| 公网带宽 | 按使用流量 或 固定 1~3Mbps | 文本站，流量很小 |
| 安全组 | 只开 **22 / 80 / 443** | 8001 和 3306 绝不能对公网开 |

**别选「经济型 e」这类共享型实例**：它的 CPU 算力会被同宿主机邻居抢占，而代码沙箱判定
用的是 **5 秒超时**——CPU 被抢时学生明明正确的代码会被判「运行超时」，还很难排查。
多花几块钱选独享型（u1）更省心。

2GiB 内存的机器，脚本会自动加 2GB swap 兜底（MySQL 8 + pandas 常驻已接近 2GB，
不加的话学生跑一段 numpy 代码就可能被 OOM killer 杀掉后端，表现成「网站突然打不开」）。

---

## 1. 一键部署（约 10 分钟）

### 1.1 本地准备好代码

```bash
cd D:/PythonProject/SoftwareEngineeringWebsite
git add -A && git commit -m "feat: 公网部署改造（注册登录 / 沙箱白名单 / 限流）"
git push origin main
```

### 1.2 上传到服务器

在**自己电脑**上执行（把 `1.2.3.4` 换成服务器公网 IP）：

```bash
# 方式一：服务器直接从 GitHub 拉（推荐，公开仓库可以直接拉）
ssh root@1.2.3.4
apt-get update && apt-get install -y git
git clone https://github.com/Dayword/liu-aochi.git /root/liu-aochi
cd /root/liu-aochi && sudo bash deploy/deploy.sh 1.2.3.4     # 有域名就写域名

# 方式二：本地直接传（不想走 GitHub 时）
scp -r D:/PythonProject/SoftwareEngineeringWebsite root@1.2.3.4:/root/liu-aochi
```

脚本会自动完成：装依赖 → 建 `ca` 用户 → 建数据库和独立账号 → 生成随机 `SECRET_KEY`
→ 关闭直通登录 → 构建前端 → 装 systemd + Nginx → 启动。

> ⚠️ 国内服务器拉 GitHub 可能超时。实在拉不动就用方式二，或先在本机 `npm run build`
> 再把 `dist` 一起传上去。

### 1.3 验证

浏览器打开 `http://你的IP/`：

1. 应该看到**登录页**（不是直接进首页）。
2. 点「注册」，建个账号 → 进入新手村创建角色 → 进首页。
3. 打开 `/api/health`，确认返回：

```json
{"status":"ok","env":"prod","guest_login":false,"code_run":true,"config_warnings":[]}
```

`config_warnings` 为空数组最重要 —— 非空说明还有安全隐患，按提示改 `.env` 后
`systemctl restart code-adventurer`。

---

## 2. 手动部署（不想用脚本时）

```bash
# 依赖
apt install -y python3-venv nginx mysql-server rsync
curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt install -y nodejs

# 用户与目录
useradd --system --create-home --shell /usr/sbin/nologin ca
rsync -a --exclude node_modules --exclude venv --exclude .env \
  /root/liu-aochi/ /opt/code-adventurer/
chown -R ca:ca /opt/code-adventurer

# 后端
python3 -m venv /opt/code-adventurer/venv
/opt/code-adventurer/venv/bin/pip install -r /opt/code-adventurer/backend/requirements.txt

# 数据库
mysql -uroot -e "CREATE DATABASE code_adventurer DEFAULT CHARACTER SET utf8mb4;
  CREATE USER 'ca_app'@'127.0.0.1' IDENTIFIED BY '强密码';
  GRANT ALL ON code_adventurer.* TO 'ca_app'@'127.0.0.1';"

# 配置
cp /opt/code-adventurer/backend/.env.production.example /opt/code-adventurer/backend/.env
vim /opt/code-adventurer/backend/.env      # 改 DB_URL / SECRET_KEY / CORS_ORIGINS
chmod 600 /opt/code-adventurer/backend/.env && chown ca:ca /opt/code-adventurer/backend/.env

# 前端
cd /opt/code-adventurer/frontend && npm ci && npm run build
mkdir -p /var/www/code-adventurer && rsync -a --delete dist/ /var/www/code-adventurer/dist/

# 服务
cp deploy/code-adventurer.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now code-adventurer

# Nginx
sed 's/server_name your-domain.com;/server_name 1.2.3.4;/' deploy/nginx.conf \
  > /etc/nginx/sites-available/code-adventurer
ln -sf /etc/nginx/sites-available/code-adventurer /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

---

## 3. HTTPS（可选但建议）

有域名后：

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com        # 自动改 Nginx 配置并续期
```

只有 IP、没有域名时可以用自签证书，但浏览器会报「不安全」，反而不如 HTTP。
**面试演示用 HTTP + IP 完全可以**，只要不让人输入密码（本站密码是学习账号，风险可控）。

---

## 4. 安全清单（上线前逐条确认）

| 项目 | 怎么确认 | 为什么 |
|---|---|---|
| `ALLOW_GUEST_LOGIN=false` | `/api/health` 里 `guest_login: false` | 否则所有人共享同一账号，进度互相覆盖 |
| `SECRET_KEY` 是随机的 | `/api/health` 的 `config_warnings` 为空 | 默认密钥 = 任何人都能伪造任何人的登录态 |
| `ENV=prod` | 同上 | 触发上面的自检 |
| `CORS_ORIGINS` 不是 `*` | `.env` | 防止别的站拿你后端当免费 API |
| MySQL 只监听 127.0.0.1 | `ss -lntp \| grep 3306` | 不要对公网开 3306 |
| `.env` 权限 600 | `ls -l backend/.env` | 里面有 AI Key 和库密码 |
| 云厂商安全组只开 22/80/443 | 控制台 | 8001 和 3306 绝不能对公网开放 |
| 沙箱残余风险已知 | 见下 | 文本层防护挡不住所有逃逸 |

### 关于代码沙箱的诚实说明

现在的防护是四层：AST 模块白名单 → 高危名字拦截 → 子进程资源限制（内存/CPU/文件大小）
+ `unshare -n` 断网 + 最小化环境变量（**AI Key 不会传给子进程**）→ 输出截断 + 频率限制。

它能挡住绝大多数误用和脚本小子的尝试，但**不是安全边界**：理论上仍可通过字符串拼接
访问危险属性逃逸。因此：

- 只想给人演示学习功能 → 保持 `CODE_RUN_ENABLED=true`，够用；
- 要长期挂在公网、担心被盯上 → 设 `CODE_RUN_ENABLED=false`（课程判定不受影响，
  只是失去「自由运行代码」这个入口），或按设计方案换 Judge0/Docker 隔离。

### 关于 AI 成本

`AI_API_KEY` 一旦配上，每个访客的对话、错题解析、面试评分都在花你的钱。
已加两层限流（Nginx 30 次/分/IP + 应用内 15 次/分/用户），但仍建议：

- 用有额度上限的 Key，别用绑了信用卡的；
- 或者在模型后台设日消费上限；
- 演示期可以直接留空 `AI_API_KEY` —— 会走离线规则引擎，全部功能仍可跑通，零成本。

---

## 5. 日常运维

```bash
systemctl status code-adventurer        # 看服务状态
journalctl -u code-adventurer -f        # 实时日志
systemctl restart code-adventurer       # 重启（改完 .env 必须重启）
tail -f /var/log/nginx/code-adventurer.error.log

# 更新代码（本地推送后，在服务器上）
cd /opt/code-adventurer && git pull    # 或重新 rsync
/opt/code-adventurer/venv/bin/pip install -r backend/requirements.txt
cd frontend && npm run build && rsync -a --delete dist/ /var/www/code-adventurer/dist/
systemctl restart code-adventurer && systemctl reload nginx
```

### 备份数据库

```bash
mkdir -p /root/backup
mysqldump -uroot code_adventurer | gzip > /root/backup/ca_$(date +%F).sql.gz
# 加到 crontab：0 4 * * * 上面这行
```

### 常见故障

| 现象 | 排查 |
|---|---|
| 打开是 Nginx 默认页 | `sites-enabled/default` 没删，或 `nginx -t` 有报错 |
| 502 Bad Gateway | 后端没起来：`journalctl -u code-adventurer -n 50`。多半是 `.env` 数据库密码错 |
| 刷新 /learn 变 404 | Nginx 缺 `try_files $uri $uri/ /index.html`（本仓库配置已含） |
| 登录一直转圈 | 前端产物里的 `/api` 打到了别的地址：检查是否用了 `VITE_API_BASE` |
| AI 回复像模板 | Key 没生效，服务端静默降级了。用 `python ai_health_check.py` 验证 5 个功能真假 |
| 429 太多 | 自己调试被限流了：把 `CODE_RUN_PER_MINUTE` / `AI_CALL_PER_MINUTE` 调大后重启 |

---

## 6. 回滚

部署前打 tag，出问题直接切回：

```bash
cd /opt/code-adventurer && git log --oneline -5
git checkout <上一个提交>
systemctl restart code-adventurer
```

数据库结构由 SQLAlchemy `create_all` 自动补表（只增不删），回滚代码不会破坏数据；
但如果新版本改过表结构，回滚前先按上面方式备份。
