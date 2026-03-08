# Instagram移动客户端网络流量截获 - 解题过程

## 实验题目

使用Instagram手机客户端，搜索 `access newswire`，截获 `*.instagram.com`或 `*.fbcdn.net`请求的**完整域名（包含子域名）**和**IP地址**。

---

## 环境搭建

### 网络拓扑

```
iPad (Instagram App)
     ↓
电脑热点 (WiFi)
     ↓
mitmproxy (端口8080)
     ↓
小火箭
     ↓
Instagram服务器
```

### 配置

#### 启动mitmproxy

```bash
mitmweb --listen-host 0.0.0.0 --listen-port 8080
```

#### 配置iPad

1. iPad连接电脑WiFi热点
2. 配置HTTP代理：服务器=电脑IP，端口=8080
3. 访问 `mitm.it`安装CA证书
4. 信任证书

#### 配置小火箭

添加代理服务器配置，启用全局代理。

---

## 抓包

### Wireshark

1. 打开Wireshark
2. 选择网卡：**本地连接\*2**
3. 开始抓包

### iPad操作

1. 打开Instagram
2. 搜索：`access newswire`
3. 点进结果页
4. 浏览图片/视频

---

## 数据提取

### 步骤1：过滤DNS

过滤器：

```
dns.qry.name contains "instagram"
```

结果：

```
Standard query response gateway.instagram.com A 104.244.43.52
Standard query response gateway.instagram.com A 202.160.130.66
Standard query response gateway.instagram.com A 104.16.252.55
```

得到：

- `gateway.instagram.com` → `104.244.43.52`, `202.160.130.66`, `104.16.252.55`

---

### 步骤2：frame过滤器

过滤器：

```
frame contains "instagram"
```

结果：

```
CONNECT i.instagram.com:443
TLS Client Hello (SNI=i.instagram.com)
CONNECT scontent-sjc3-1.cdninstagram.com:443
TLS Client Hello (SNI=scontent-sjc3-1.cdninstagram.com)
```

得到域名：

- `i.instagram.com`
- `scontent-sjc3-1.cdninstagram.com`

（无DNS响应包，无法获取IP）

---

### 步骤3：过滤fbcdn

过滤器：

```
frame contains "fbcdn"
```

结果：

```
Standard query response netseer-ipaddr-assoc.xz.fbcdn.net A 157.240.9.34
```

得到：

- `netseer-ipaddr-assoc.xz.fbcdn.net` → `157.240.9.34`

---

### 步骤4：nslookup补充IP

#### 查询i.instagram.com

```bash
nslookup i.instagram.com
```

结果：

```
C:\Users\48842>nslookup i.instagram.com
服务器: UnKnown
Address: 2001:da8:255:11:202:205:208:6

名称: i.instagram.com
Addresses: 2a03:2880:f117:83:face:b00c:0:25de
          69.63.184.30
```

得到：`i.instagram.com` → `69.63.184.30`

#### 查询scontent-sjc3-1.cdninstagram.com

```bash
nslookup scontent-sjc3-1.cdninstagram.com
```

结果：

```
C:\Users\48842>nslookup scontent-sjc3-1.cdninstagram.com
服务器: UnKnown
Address: 2001:da8:255:11:202:205:208:6

名称: scontent-sjc3-1.cdninstagram.com
Addresses: 2a03:2880:f112:83:face:b00c:0:25de
          31.13.94.36
```

得到：`scontent-sjc3-1.cdninstagram.com` → `31.13.94.36`

---

## 最终答案

| 完整域名                          | IP地址         |
| --------------------------------- | -------------- |
| gateway.instagram.com             | 104.244.43.52  |
| gateway.instagram.com             | 202.160.130.66 |
| gateway.instagram.com             | 104.16.252.55  |
| i.instagram.com                   | 69.63.184.30   |
| scontent-sjc3-1.cdninstagram.com  | 31.13.94.36    |
| netseer-ipaddr-assoc.xz.fbcdn.net | 157.240.9.34   |

### 域名分类

- **网关服务器**：`gateway.instagram.com`（3个IP，负载均衡）
- **API服务器**：`i.instagram.com`（处理搜索、获取内容）
- **Instagram CDN**：`scontent-sjc3-1.cdninstagram.com`（图片/视频，sjc3=San Jose数据中心）
- **Facebook CDN**：`netseer-ipaddr-assoc.xz.fbcdn.net`（Meta共享基础设施）
