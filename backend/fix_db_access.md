# 数据库访问配置修复指南

## 问题描述
从本地Windows机器连接远程PostgreSQL数据库时出现连接超时，但在服务器本地可以正常连接。

## 可能的原因

### 1. PostgreSQL 监听地址配置
PostgreSQL可能只监听 `127.0.0.1`（本地），而不是 `0.0.0.0`（所有接口）。

**检查方法：**
```bash
# 在服务器上执行
sudo grep listen_addresses /etc/postgresql/*/main/postgresql.conf
# 或
sudo grep listen_addresses /var/lib/pgsql/*/data/postgresql.conf
```

**修复方法：**
编辑 `postgresql.conf`：
```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
# 或
sudo nano /var/lib/pgsql/*/data/postgresql.conf
```

找到并修改：
```
# 修改前
listen_addresses = 'localhost'  # 或 '127.0.0.1'

# 修改后
listen_addresses = '*'  # 监听所有接口
# 或
listen_addresses = '0.0.0.0'  # 监听所有IPv4接口
```

重启PostgreSQL：
```bash
sudo systemctl restart postgresql
# 或
sudo service postgresql restart
```

### 2. pg_hba.conf 客户端认证配置
可能只允许本地连接，需要添加远程连接规则。

**检查方法：**
```bash
sudo cat /etc/postgresql/*/main/pg_hba.conf | grep -v "^#" | grep -v "^$"
```

**修复方法：**
编辑 `pg_hba.conf`：
```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

添加允许远程连接的规则（在文件末尾）：
```
# 允许特定IP访问（推荐）
host    all             all             你的本地IP/32         md5

# 或允许所有IP访问（不推荐，安全性较低）
host    all             all             0.0.0.0/0              md5
```

重新加载配置（无需重启）：
```bash
sudo systemctl reload postgresql
# 或
sudo -u postgres psql -c "SELECT pg_reload_conf();"
```

### 3. 防火墙规则
服务器防火墙可能阻止了外部访问。

**检查防火墙状态：**
```bash
# UFW
sudo ufw status

# Firewalld
sudo firewall-cmd --list-all

# iptables
sudo iptables -L -n | grep 50511
```

**添加防火墙规则：**
```bash
# UFW
sudo ufw allow 50511/tcp

# Firewalld
sudo firewall-cmd --permanent --add-port=50511/tcp
sudo firewall-cmd --reload

# iptables
sudo iptables -A INPUT -p tcp --dport 50511 -j ACCEPT
sudo iptables-save
```

### 4. 云服务器安全组规则
如果使用阿里云、腾讯云等云服务器，需要检查安全组规则。

**阿里云：**
1. 登录阿里云控制台
2. 进入 ECS -> 网络与安全 -> 安全组
3. 找到对应的安全组，添加入站规则：
   - 端口：50511
   - 协议：TCP
   - 授权对象：你的本地IP或 0.0.0.0/0（不推荐）

**腾讯云：**
1. 登录腾讯云控制台
2. 进入 CVM -> 安全组
3. 添加入站规则：端口50511，协议TCP

## 快速诊断命令

在服务器上运行：
```bash
# 1. 检查监听地址
sudo netstat -tlnp | grep 50511
# 应该看到 0.0.0.0:50511 或 :::50511，而不是 127.0.0.1:50511

# 2. 检查PostgreSQL配置
sudo grep listen_addresses /etc/postgresql/*/main/postgresql.conf

# 3. 检查pg_hba.conf
sudo grep -E "^host|^local" /etc/postgresql/*/main/pg_hba.conf | grep -v "^#"

# 4. 测试本地连接
psql -h 127.0.0.1 -p 50511 -U postgres -d app

# 5. 测试监听所有接口的连接
psql -h 0.0.0.0 -p 50511 -U postgres -d app
```

## 安全建议

1. **不要使用 0.0.0.0/0**：只允许特定IP访问
2. **使用SSL连接**：配置PostgreSQL使用SSL
3. **强密码**：确保数据库密码足够强
4. **定期更新**：保持PostgreSQL版本更新
5. **监控日志**：定期检查PostgreSQL日志文件

## 验证修复

修复后，从本地Windows机器测试：
```powershell
# PowerShell
Test-NetConnection -ComputerName 8.145.33.61 -Port 50511

# 或使用Python
python -c "import socket; s = socket.socket(); s.settimeout(10); result = s.connect_ex(('8.145.33.61', 50511)); print('OK' if result == 0 else 'FAIL'); s.close()"
```

如果连接成功，后端服务应该可以正常连接数据库。
