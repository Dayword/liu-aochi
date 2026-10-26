# 公网部署指南（让人在局域网外也能访问）

> 目标读者：自己的电脑上跑得好好的，现在想让别人（面试官、同学、HR）直接打开链接就能用。

---

## ⭐ 最省事的部署方式（2C2G 小机器首选，全程 5 分钟）

**核心思路：服务器只做「安装」，不做「构建」。**

为什么这条最可靠 —— 前几次踩的坑都出在同一处：

| 现象 | 真实原因 |
|---|---|
| 阿里云推送「系统盘吞吐达到上限 `SysDisBPS`」 | `npm ci` 要解压/写入**上万个**小文件，40GiB ESSD Entry（最低档盘）扛不住 |
| SSH 连上了、两分钟不出现密码提示 | 磁盘被打满时进程进 D 状态，`sshd` 一起排队，banner 发不出来 |
| 部署跑到一半 SSH 断线，前功尽弃 | 前台跑长脚本，网络一抖就被杀 |
| 2G 内存 OOM，安骑士/后端被 Killed | `npm ci` + `vite build` 和 MySQL、uvicorn 抢内存 |

而**前端产物只有 2.3MB / 7 个文件**。放在本机构建、把成品传上去，服务器完全不需要 Node，上述四条一次性全部消失。

### 四步命令

```bash
# ① 本机（项目根目录）：构建前端 + 打包，产物 ca-deploy.tar.gz 约 5.4MB
bash scripts/pack.sh

# ② 本机：传到服务器
scp ca-deploy.tar.gz root@39.96.223.77:/root/

# ③ 服务器：解包
ssh root@39.96.223.77
mkdir -p /root/liu-aochi && tar -xzf /root/ca-deploy.tar.gz -C /root/liu-aochi

# ④ 服务器：装（2~3 分钟，注意最后那个 --skip-build）
cd /root/liu-aochi && sudo bash deploy/deploy.sh 39.96.223.77 --skip-build
```

看到 `✅ 部署完成` 后验证：

```bash
systemctl is-active code-adventurer nginx mysql   # 三个 active
curl -s http://127.0.0.1:8001/api/health          # guest_login:false, config_warnings:[]
```

浏览器打开 `http://39.96.223.77/` → 注册（用户名 ≥3 位、密码 ≥6 位）→ 建角色 → 开始用。

### 三个补充说明

- **`--skip-build` 做什么**：跳过安装 Node、跳过 `npm ci` 和 `vite build`，直接把包里的
  `frontend/dist` 拷到 `/var/www/code-adventurer/dist`。其余（MySQL 建库、随机密钥、
  关直通登录、swap、systemd、Nginx）完全一样。
- **以后更新代码**：重复 ①②③④ 即可。脚本是幂等的，数据库和 `.env` 都会保留，
  不会冲掉已有账号和进度。
- **忘了 `--skip-build` 会怎样**：包里有 `frontend/dist`，但脚本会走默认分支去
  `npm ci`，等于白等 10 分钟并重新踩一遍磁盘坑。**这条一定要带上。**

### 想用域名

把第 ④ 步换成（域名解析要先指向这台机器）：

```bash
sudo bash deploy/deploy.sh hongchi.xyz --https --skip-build
```

大陆服务器走域名需要 ICP 备案，详见第 3 节。

---

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

#### 预装应用下拉只有 宝塔/WordPress/Docker/LNMP 怎么办

阿里云有时不提供「无」。这四个里**只有 Docker 不会和本脚本打架**：

| 选项 | 能否用 | 原因 |
|---|---|---|
| 宝塔面板 | ❌ | 自装 Nginx+MySQL，占 8888，与脚本抢 80/3306 |
| LNMP | ❌ | 正是脚本要装的那套，冲突最彻底 |
| WordPress | ❌ | 还要 PHP + 独立数据库，占用最多 |
| Docker | ✅ | 只装 engine，不动 80/3306；脚本会自动停掉它省内存 |

`deploy.sh` 已内置处理：检测到 Docker 就 `systemctl disable --now docker`（本项目全是
裸进程、不用容器，dockerd 白占 100~150MB）；检测到宝塔会明确告警让你重装系统。

#### 能不能关机省钱？

技术上可以，`deploy.sh` 已经 `systemctl enable` 了 MySQL / 后端 / Nginx，**开机后服务会自动恢复**。
按量付费的「节省停机模式」下，关机通常不再收 CPU/内存费用，但**系统盘（40G ESSD）一般继续计费**，
约 ¥10/月。具体看订单页的计费说明。

但有两个真实代价，决定了它不适合「发给别人看的链接」：

1. **关机期间网站直接打不开**。面试官/HR 在你关机的时段点开链接，看到的是浏览器超时——
   这比没有链接更糟。
2. **公网 IP 可能变**。按量付费实例停机再开机，公网 IP 往往会重新分配（除非绑了固定 EIP）。
   IP 一变，你之前发出去的链接全部失效，还得重新发给每个人。

所以：**只给自己阶段性开发** → 可以关；**链接要发给面试官** → 老老实实开着。
真想省钱，选 2vCPU 2GiB（价格约为 4GiB 的 48%，能多撑约 1.5 个月）比关机划算得多。

#### 共享型实例（经济型 e）的一个坑

经济型 e 是共享算力，CPU 会被同宿主机邻居抢占。本项目的代码判定最初是 5 秒超时，
CPU 一被抢，学生**明明正确的代码会被判「运行超时」**，而这种误判几乎没人会想到是机器的问题。
`deploy.sh` 生成的生产 `.env` 里已把 `CODE_RUN_TIMEOUT` 放宽到 10 秒（正常代码 0.1 秒跑完，
放宽只是让死循环多等 5 秒）。

---

## 快速路径：只用公网 IP 上线（约 10 分钟，不碰域名）

> 这条是给「现在就想要一个能发出去的链接」用的。**不需要域名、不需要备案**，
> 纯 IP 访问不受 ICP 约束。等以后要长期挂简历再回头做第 3 节。
> 全程只需一台服务器 + 你的笔记本。

### 步骤 0：先确认两件事（30 秒）

在你的笔记本浏览器里打开阿里云 ECS 控制台 → 这台实例 → 「安全组」：

- 入方向放行 **22**（SSH）、**80**（网站）。`8001` 和 `3306` **不要放行**，
  后端和数据库只应监听 127.0.0.1，走 Nginx 反代进来。
- 记下公网 IP（本文示例用 `39.96.223.77`，换成你自己的）。

### 步骤 1：连上服务器，拉代码

```bash
ssh root@39.96.223.77
apt-get update && apt-get install -y git
git clone https://github.com/Dayword/liu-aochi.git /root/liu-aochi
```

> 国内服务器拉 GitHub 经常超时。拉不动就在**你电脑上**用
> `scp -r D:/PythonProject/SoftwareEngineeringWebsite root@39.96.223.77:/root/liu-aochi` 传上去。

> ⚠️ **连不上服务器的三种情况，别混在一起判断**：
> - 报「**连接超时 / Connection timed out**」→ 安全组没放行 22。路径：ECS 控制台 →
>   实例 ID → 「安全组」→ 点安全组 ID → 「配置规则」→ 入方向 → 手动添加
>   `22/22`，授权对象 `0.0.0.0/0`（调试阶段先全开，稳定后改成自己的 IP）。
>   保存即刻生效、不用重启。网站还要再放行 `80/80`，建议一次加两条。
> - 报「**无法使用密码登录方式 / Permission denied**」→ 认证被关掉了。在控制台
>   「重置密码」→ **重启实例**（不重启不生效）→ 再连。仍不行就用「通过 VNC 连接」进系统，
>   把 `/etc/ssh/sshd_config.d/` 里的 `PasswordAuthentication no` 改成 `yes`，
>   然后 `systemctl restart ssh`。
> - **连的是 `172.x.x.x` 这种地址** → 那是私网 IP，只有同一 VPC 内能通。
>   自己电脑上必须用公网 IP（控制台实例列表上显示的那个）。
>
> 另：阿里云控制台「远程连接」弹窗里预填的常是私网 IP，别照抄。
>
> **安全组放行后仍超时的备选方案**：直接用控制台「通过 VNC 连接实例」进系统，
> VNC 走阿里云内部通道，不经过安全组、也不需要 SSH 认证，装完再看 80 是否可达。

### 步骤 2：一条命令装完

```bash
cd /root/liu-aochi && sudo bash deploy/deploy.sh 39.96.223.77
```

> ⚠️ **别在 SSH 前台直接跑**：按这个顺序跑 5~8 分钟，中途网断了（笔记合盖、
> WiFi 抖动、手机热点切回）SSH 会话一断，脚本会被 SIGHUP 杀掉，留下装了一半的状态。
> 稳妥写法是后台跑 + 跟日志：
>
> ```bash
> cd /root/liu-aochi
> nohup bash deploy/deploy.sh 39.96.223.77 > /root/deploy.log 2>&1 &
> tail -f /root/deploy.log        # 看进度，Ctrl+C 只是退出查看，不会中断部署
> ```
>
> 断线重连后再 `tail -f /root/deploy.log` 继续看；看到 `✅ 部署完成` 就好。

约 5~8 分钟（大部分时间在装 `numpy/pandas` 和构建前端）。脚本会自动装 Nginx / MySQL /
Python 依赖、建库建账号、生成随机密钥、**关闭直通登录**、配置 2GB swap、停掉预装 Docker。

### 步骤 3：验证（3 条命令，别跳过）

```bash
curl -s http://127.0.0.1:8001/api/health          # 后端活着
curl -s http://127.0.0.1/api/health | head -c 300  # Nginx 反代通了
systemctl is-active code-adventurer nginx mysql    # 三个都应是 active
```

第一条返回里重点看两个字段：

```json
{"status":"ok","env":"prod","guest_login":false,"code_run":true,"config_warnings":[]}
```

- `guest_login` 必须是 `false`（否则所有人共享同一账号）
- `config_warnings` 必须是**空数组**（非空就是还有隐患，按提示改 `.env` 后
  `systemctl restart code-adventurer`）

然后浏览器打开 `http://39.96.223.77/`，应该看到**登录页**，不是首页。

### 步骤 4：注册你的账号

点「注册」→ 填用户名 + 密码（**用户名 ≥3 位，密码 ≥6 位**）→ 自动跳到建角色页 → 填角色名、身份、方向
→ 进首页。到此链接已经可以发给别人了。

> ⚠️ **登录报「用户名或密码错误」时，先确认账号是否存在**——服务器和你本机是两个独立的库，
> 你本机的账号（包括「如梦令」）在服务器上**默认不存在**。而且接口对「用户不存在」和
> 「密码错」返回同一句提示，光看报错分不出来：
>
> ```bash
> sudo mysql -e "SELECT id, username FROM code_adventurer.users;"
> ```
>
> 空表 → 先注册；有 `如梦令` → 密码是早期随机生成的，跑步骤 5⑤ 的 `reset_password.py`。

### 步骤 5（可选但强烈建议）：把本地真实进度搬上去

服务器是**全新的空库**，你现在登录进去是个 Lv.1 新号。如果你想给面试官看真实进度
（8 门 Python 已掌握、Lv.3、金币、面试记录），把本地库导过去：

**① 在本机导出**（Windows，路径按你实际安装位置改）：

```bash
cd /d/PythonProject/SoftwareEngineeringWebsite
"/d/MySQL/MySQL Server 8.0/bin/mysqldump" -uroot -proot \
  --default-character-set=utf8mb4 --single-transaction --no-tablespaces \
  --skip-add-locks --result-file=D:/ca_local.sql code_adventurer
```

> 用 `--result-file` 而不是 `> 文件`，Windows 下重定向容易把中文搞乱。

**② 传到服务器**：

```bash
scp D:/ca_local.sql root@39.96.223.77:/root/
```

**③ 在服务器上导入**：

```bash
mysql --default-character-set=utf8mb4 code_adventurer < /root/ca_local.sql
```

> ⚠️ **`--default-character-set=utf8mb4` 不能省**。少了这一句，中文会被按本地编码
> 解析，报 `ERROR at line N: Unknown command '\''`，而且只导入一半——实测踩过。
> 导入是**覆盖式**的（含 `DROP TABLE`），所以要在别人注册之前做；做砸了就重跑
> `deploy.sh` 会重建表结构，再导一次即可。

**④ 清掉冒烟测试留下的账号**：本地库里有 50 多个 `tester1789…` / `grader…` 之类的
测试账号，导上去排行榜会很脏。清到只剩你自己的两个：

```bash
mysql --default-character-set=utf8mb4 code_adventurer <<'SQL'
SET FOREIGN_KEY_CHECKS=0;
DELETE FROM users WHERE username NOT IN ('如梦令','demo');
DELETE FROM characters WHERE user_id NOT IN (SELECT id FROM users);
SET FOREIGN_KEY_CHECKS=1;
SELECT id, username FROM users;
SQL
```

执行完应该只剩 `demo` 和 `如梦令` 两行。

**⑤ 改主账号密码**（最重要的一步）：

「如梦令」的密码是早期直通登录随机生成的，**没人知道**，不改就登不进去，
你会以为进度全丢了：

```bash
cd /opt/code-adventurer/backend
/opt/code-adventurer/venv/bin/python reset_password.py --list
/opt/code-adventurer/venv/bin/python reset_password.py 如梦令 你的新密码
```

然后回浏览器用 `如梦令` + 新密码登录，应该看到 Lv.3 / 282 金币 / 8 门已掌握。

### 步骤 6：把链接发出去

```
http://39.96.223.77/
```

发给面试官时建议加一句「账号可直接注册，也可以用 demo / 演示」。**别把「如梦令」
的密码写进简历或聊天里**——那是你的真实数据，别人登进去能改。

### 这一步的常见故障

| 现象 | 原因 | 怎么查 |
|---|---|---|
| 浏览器一直转圈 | 安全组没放行 80 | 控制台安全组；`ss -lntp \| grep :80` |
| 502 Bad Gateway | 后端没起来 | `systemctl status code-adventurer` + `journalctl -u code-adventurer -n 50` |
| 打开是登录页但登录报错 | 数据库没连上 | `tail -f /var/log/nginx/code-adventurer.error.log` |
| **注册/登录返回 500**，首页正常 | **bcrypt 被装成 5.x**，与 passlib 1.7.4 不兼容 | `journalctl -u code-adventurer -n 40 \| grep -i bcrypt`，看到 `password cannot be longer than 72 bytes` 即是。修：`venv/bin/pip install "bcrypt>=4.0.1,<5"` 后重启。**requirements.txt 已写死 `<5`**，用最新包部署不会遇到 |
| 页面能开、注册后白屏 | 前端构建产物没同步 | `ls /var/www/code-adventurer/dist` |
| 导入数据后中文变问号 | 少了 `--default-character-set=utf8mb4` | 重新导一次 |
| 服务器重启后网站打不开 | 服务没设开机自启 | `systemctl is-enabled code-adventurer nginx mysql` |

> 排 `502` 时注意：**本机 `curl 127.0.0.1:8001` 通、`curl 127.0.0.1` 不通**，说明问题在
> Nginx 而不在后端，直接看 `nginx -t` 和 error.log。

### 部署后阿里云报「实例存在 3 项异常」，要不要慌？

**不用。** 每次在这台机器上跑 `deploy.sh`，控制台的「实例自助诊断」基本都会弹这三条，
它们全是**部署过程的副作用**，不是故障：

| 告警 | 真正原因 | 处理 |
|---|---|---|
| CPU 负载达到 97% | `npm run build` 打包 + `pip install numpy/pandas` | 忽略，构建完 1 分钟就降 |
| 云盘读写 IOPS 达上限 | 上述两步写几千个小文件，**40GiB ESSD Entry 只有 2120 IOPS**，是全系最低档 | 忽略，只是装得慢 |
| 安骑士（AliYunDun）离线 | 心跳超时；2G 机器上更可能是**内存不足被 OOM killer 挤掉** | `systemctl restart aliyun-service`，反复离线就把 `CODE_RUN_ENABLED` 设 false 省内存 |

判断「真出事」还是「虚惊」只看三条命令：

```bash
systemctl is-active code-adventurer nginx mysql   # 三个 active = 站点没问题
dmesg -T | grep -i "killed process" | tail -10    # 有无 OOM；杀到 python/node 才会影响
free -h && df -h / && swapon --show               # swap 应有 2.0Gi
```

> 想彻底避开这几条告警：在**本地** `npm run build`，把 `dist` 和整个目录一起
> `scp` 上去，服务器上就不会跑构建（见 1.2 方式二）。缺点是每次改代码都要重传。

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
cd /root/liu-aochi && sudo bash deploy/deploy.sh 1.2.3.4
# 有域名就写域名；域名解析生效 + 备案通过后加 --https 申请证书：
#   sudo bash deploy/deploy.sh hongchi.xyz
#   sudo bash deploy/deploy.sh hongchi.xyz --https   ← 见第 3 节

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

## 3. 接入域名（hongchi.xyz）

### 3.1 第一步：加解析记录

到域名服务商的「DNS 解析」里加两条 A 记录（TTL 600）：

| 主机记录 | 记录类型 | 记录值 |
|---|---|---|
| `@` | A | 你的服务器公网 IP |
| `www` | A | 你的服务器公网 IP |

验证（在**自己电脑**上，不是服务器）：

```bash
nslookup hongchi.xyz        # Windows
dig +short hongchi.xyz      # macOS / Linux
```

返回的 IP 和服务器一致才继续。`deploy.sh` 会先做这一步预检并提示，解析没生效时
脚本仍会装完站点，但证书申请一定失败——所以别跳过。

### 3.2 ⚠️ 第二步：大陆服务器必须先 ICP 备案

**这是 .xyz 用在大陆服务器上的硬门槛，跟证书无关。** 域名解析到大陆 IP 但没备案，
阿里云/运营商会拦截 80/443，浏览器看到的是「该网站暂时无法访问」的拦截页，
不是你的站点。备案没下来之前，`certbot` 也一定失败。

`.xyz` 后缀本身是**可以**备案的——工信部 2016 年就批复了 XYZ.COM LLC，
它在阿里云公示的「其他顶级域名」列表里（`.XYZ` 明文在列）。真正卡人的是下面三条，
缺一条都过不了核验：

| 要求 | 你要确认的 |
|---|---|
| 顶级域已获工信部批复 | `.xyz` ✅ 满足 |
| **注册商是已批复的境内机构** | ⚠️ 关键：域名在 Namecheap / GoDaddy / Cloudflare / NameSilo 等**境外注册商**注册的，**不能直接备案**，必须先「域名转入」阿里云/腾讯云（转入含续费 1 年，几十块，需 5~7 天） |
| 域名实名信息 = 备案主体 | 个人备案：持有人姓名+身份证号必须是你本人；实名改了要等 2~3 天同步到工信部库才能提交 |
| 域名有效期 > 45 天 | 快到期先续费 |

还有一条是服务器侧，**这条最容易踩**：阿里云要求备案服务器必须是
**包年包月、购买时长 > 3 个月、且已开通公网带宽**。

> ⚠️ **按量付费实例不支持申请备案服务码**，免费试用的 ECS 也不算数。
> 如果你那台是「¥0.12/小时」按量计费或试用额度包，到备案系统里会**选不到实例**，
> 提示「产品信息无效」。解决方式：把实例**转为包年包月并至少买 3 个月**
> （控制台 → 实例 → 更多 → 计费方式转换），转完立刻能申请服务码。
> 不想转就改买一台包年 3 个月的轻量应用服务器专门用来备案。

流程与耗时（阿里云 App，全程手机可办）：

1. 域名转入 + 实名（若已在境内注册商则跳过）——5~7 天
2. 阿里云「ICP 备案」提交：主体信息 → 网站信息 → 上传身份证/核验单 → 人脸核验（代替老式幕布）
3. 阿里云初审 —— 1~2 个工作日
4. 管局审核 —— 一般 1~3 周（河北管局）
5. 通过后拿到 `冀ICP备XXXXXXXX号`，**把备案号放到页面底部**：

```bash
ICP_BEIAN="冀ICP备2026xxxxxx号-1" sudo bash deploy/deploy.sh hongchi.xyz --https
```

脚本会把备案号写进 `frontend/.env.production`（`VITE_ICP_BEIAN`），构建后自动渲染成
页面底部的链接，指向 `beian.miit.gov.cn`。不配置就不显示，本地开发不受影响。

> 备案期间网站**不能关**，但也不能对外提供服务，所以阿里云会给一个临时访问方式。
> 实务上：**备案期间用 IP 访问，备案通过后再切域名**，这样你能马上发给别人看。

### 3.3 第三步：一条命令启用 HTTPS

解析生效 + 备案通过后，在服务器上重跑：

```bash
cd /root/liu-aochi && git pull
sudo bash deploy/deploy.sh hongchi.xyz --https
```

脚本会：把 `server_name` 改成 `hongchi.xyz www.hongchi.xyz` → 更新 `CORS_ORIGINS`
→ `certbot --nginx` 签发证书 → 把 80 自动重定向到 443 → 启用 `certbot.timer`
自动续期（90 天证书，到期前 30 天自动续，不用管）。

域名解析了 www 但证书只想要裸域？脚本会自动检测 `www.hongchi.xyz` 是否也指向本机，
没指向就只签裸域，避免 certbot 因「www 解析不到」整体失败。

**关于 .xyz 的信誉**：个别邮箱/安全产品对新顶级域有偏见，可能把通知邮件判垃圾。
不影响 HTTPS 和浏览器访问，但如果要做邮件发信，建议另配 `.com`。

### 3.4 没有域名 / 不想等备案的替代路径

| 做法 | 能不能马上用 | 代价 |
|---|---|---|
| 直接用 `http://公网IP/` | ✅ 立刻 | 链接难看、无法 HTTPS、IP 可能变 |
| 服务器换**香港/境外**节点 | ✅ 立刻，域名免备案 | 大陆访问延迟多 30~80ms，且需重新部署 |
| 大陆服务器 + 非标准端口（如 8080） | ⚠️ 通常可通 | 绕过拦截不合规，且链接要带端口 |

**面试演示用 `http://IP/` 完全够**，只要不让人在里面输入真实密码（本站密码是学习账号）。
真正要长期挂在简历上，再走备案 + 域名。

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

---

## 附录 A：一条命令完成整备（推荐给"服务器状态不明"时）

适用于：之前装到一半、SSH 卡住、不确定哪些进程还在跑。整段粘贴到服务器终端
（或阿里云控制台的云助手 / VNC）执行，**它会自己清理残留 + 拉代码 + 部署 + 验证**。

```bash
cat > /root/go.sh <<'EOS'
#!/usr/bin/env bash
export DEBIAN_FRONTEND=noninteractive
IP=39.96.223.77                      # ← 改成你的公网 IP
DIR=/root/liu-aochi
REPO=https://github.com/Dayword/liu-aochi.git
# 国内拉 GitHub 超时的话，把下面这行注释掉、启用 ghproxy 镜像那行
# REPO=https://ghfast.top/https://github.com/Dayword/liu-aochi.git

step() { echo -e "\n========== $* =========="; }

step "1/6 现状"
uptime; free -h; df -h / | tail -1

step "2/6 清理卡死的旧进程"
pkill -f 'deploy/deploy.sh' 2>/dev/null && echo "已终止旧部署"
pkill -f 'npm ci|npm install|vite build' 2>/dev/null && echo "已终止旧构建"
sleep 2

step "3/6 安装基础工具"
apt-get update -qq
apt-get install -y -qq git curl ca-certificates >/dev/null

step "4/6 获取代码"
if [ -d "$DIR/.git" ]; then
  cd "$DIR" && (git -c http.sslVerify=false pull --ff-only || echo "⚠️ 拉取失败，沿用现有代码")
else
  git -c http.sslVerify=false clone --depth 1 "$REPO" "$DIR" || { echo "❌ 拉代码失败，检查网络"; exit 1; }
fi
cd "$DIR"

step "5/6 执行部署（5~10 分钟，期间 CPU 会打满属正常）"
bash deploy/deploy.sh "$IP"

step "6/6 验证"
systemctl is-active code-adventurer nginx mysql
curl -s -m 10 http://127.0.0.1:8001/api/health; echo
curl -s -m 10 -o /dev/null -w "本机 http://127.0.0.1/ → %{http_code}\n" http://127.0.0.1/
echo -e "\n========== 完成 =========="
EOS

nohup bash /root/go.sh > /root/deploy.log 2>&1 &
tail -f /root/deploy.log
```

`tail` 里按 `Ctrl+C` 只是退出查看，**部署仍在后台跑**。断线重连后：

```bash
tail -f /root/deploy.log          # 继续看进度
grep -E "部署完成|❌|失败" /root/deploy.log   # 只看关键行
```

日志停在哪里，问题就在哪里：

| 日志最后停在 | 含义 | 怎么办 |
|---|---|---|
| `3/6 安装基础工具` | `apt-get` 慢，通常是 40G Entry 盘 IOPS 打满 | 等，最多 10 分钟 |
| `4/6 获取代码` | 拉 GitHub 超时 | 启用 ghproxy 镜像那行，重跑 |
| `5/6` 里的 `npm ci` | 2G 机器装依赖慢，属正常 | 等，**别中断** |
| `5/6` 里的 `npm run build` | CPU 打满，正常 | 等 2 分钟 |
| 完全没输出 | 脚本没起来 | `cat /root/deploy.log` 看报错 |
