# 数据库连接问题快速修复指南

## ✅ 已确认正常的配置

1. **PostgreSQL监听配置** ✅
   - 监听地址：`0.0.0.0:50511`（所有接口）
   - 状态：正常

2. **pg_hba.conf配置** ✅
   - 远程连接规则：`host all all 0.0.0.0/0 md5`
   - 状态：正常

3. **UFW防火墙** ✅
   - 状态：inactive（未启用）
   - 不是问题

## 🔍 需要检查的项目

### 1. 检查Firewalld（如果安装了）
```bash
sudo firewall-cmd --state
sudo firewall-cmd --list-ports | grep 50511
```

如果Firewalld正在运行且没有50511端口规则，执行：
```bash
sudo firewall-cmd --permanent --add-port=50511/tcp
sudo firewall-cmd --reload
```

### 2. 检查iptables（如果使用了）
```bash
sudo iptables -L -n | grep 50511
```

### 3. ⚠️ **最重要：阿里云安全组规则**

根据服务器主机名 `iZ0jl4gvocx7myleyxtmp0Z`，这是阿里云ECS服务器。

**必须配置安全组规则：**

1. **登录阿里云控制台**
   - 访问：https://ecs.console.aliyun.com
   - 或搜索"ECS控制台"

2. **找到服务器实例**
   - 进入：ECS -> 实例与镜像 -> 实例
   - 搜索实例ID或主机名：`iZ0jl4gvocx7myleyxtmp0Z`

3. **进入安全组配置**
   - 点击实例名称进入详情页
   - 点击"安全组"标签页
   - 或点击"网络和安全组" -> "安全组ID"

4. **添加入站规则**
   - 点击安全组ID进入安全组规则页面
   - 点击"入方向"标签
   - 点击"添加安全组规则"按钮
   - 填写：
     ```
     规则方向：入方向
     授权策略：允许
     协议类型：自定义TCP
     端口范围：50511/50511
     授权对象：
       - 测试用：0.0.0.0/0（允许所有IP，不推荐生产环境）
       - 生产用：你的本地IP/32（例如：123.45.67.89/32）
     描述：PostgreSQL数据库端口
     ```
   - 点击"保存"

5. **验证规则**
   - 确认规则已添加
   - 规则立即生效，无需重启

## 🧪 测试连接

配置完成后，从本地Windows PowerShell测试：

```powershell
# 方法1：使用Test-NetConnection
Test-NetConnection -ComputerName 8.145.33.61 -Port 50511

# 方法2：使用Python
python -c "import socket; s = socket.socket(); s.settimeout(10); result = s.connect_ex(('8.145.33.61', 50511)); print('连接成功' if result == 0 else '连接失败'); s.close()"
```

**期望结果：**
- `TcpTestSucceeded: True`（Test-NetConnection）
- 或输出 `连接成功`（Python）

## 📋 完整检查清单

- [x] PostgreSQL监听所有接口
- [x] pg_hba.conf允许远程连接
- [x] UFW防火墙未启用
- [ ] Firewalld防火墙检查
- [ ] iptables规则检查
- [ ] **阿里云安全组规则配置** ⚠️ 最重要

## 🎯 最可能的原因

**阿里云安全组规则未配置** - 这是最可能的原因！

即使服务器上所有配置都正确，如果阿里云安全组没有开放50511端口，外部仍然无法连接。

## 💡 快速验证

在服务器上运行以下命令，检查是否有其他防火墙：
```bash
# 检查Firewalld
sudo firewall-cmd --state 2>/dev/null || echo "Firewalld未安装或未运行"

# 检查iptables规则
sudo iptables -L -n -v | head -20

# 检查所有监听50511的进程
sudo lsof -i :50511
```

如果以上都正常，**99%的可能性是阿里云安全组规则未配置**。
