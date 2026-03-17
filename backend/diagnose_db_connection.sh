#!/bin/bash
# 数据库连接问题诊断脚本

echo "============================================================"
echo "数据库连接问题诊断"
echo "============================================================"

# 1. 检查PostgreSQL监听状态
echo ""
echo "1. PostgreSQL 监听状态:"
sudo netstat -tlnp | grep 50511 || sudo ss -tlnp | grep 50511
echo "   [期望] 应该看到 0.0.0.0:50511 或 :::50511"

# 2. 检查pg_hba.conf配置
echo ""
echo "2. pg_hba.conf 远程连接配置:"
sudo grep -E "^host.*all.*all.*0.0.0.0" /etc/postgresql/*/main/pg_hba.conf | grep -v "^#" | head -1
if [ $? -eq 0 ]; then
    echo "   [OK] 已配置允许远程连接"
else
    echo "   [FAIL] 未找到允许远程连接的配置"
fi

# 3. 检查防火墙 - UFW
echo ""
echo "3. UFW 防火墙状态:"
if command -v ufw &> /dev/null; then
    ufw_status=$(sudo ufw status | grep -i "Status")
    echo "   $ufw_status"
    if echo "$ufw_status" | grep -qi "active"; then
        port_rule=$(sudo ufw status | grep 50511)
        if [ -z "$port_rule" ]; then
            echo "   [WARNING] 防火墙已启用，但端口50511未在规则中"
            echo "   建议执行: sudo ufw allow 50511/tcp"
        else
            echo "   [OK] 端口50511已在防火墙规则中:"
            echo "   $port_rule"
        fi
    else
        echo "   [OK] UFW防火墙未启用"
    fi
else
    echo "   [SKIP] UFW未安装"
fi

# 4. 检查防火墙 - Firewalld
echo ""
echo "4. Firewalld 防火墙状态:"
if command -v firewall-cmd &> /dev/null; then
    if sudo firewall-cmd --state 2>/dev/null | grep -qi "running"; then
        ports=$(sudo firewall-cmd --list-ports 2>/dev/null | grep 50511)
        if [ -z "$ports" ]; then
            echo "   [WARNING] Firewalld已启用，但端口50511未在规则中"
            echo "   建议执行: sudo firewall-cmd --permanent --add-port=50511/tcp && sudo firewall-cmd --reload"
        else
            echo "   [OK] 端口50511已在防火墙规则中: $ports"
        fi
    else
        echo "   [OK] Firewalld未运行"
    fi
else
    echo "   [SKIP] Firewalld未安装"
fi

# 5. 检查iptables
echo ""
echo "5. iptables 规则检查:"
if command -v iptables &> /dev/null; then
    iptables_rules=$(sudo iptables -L -n | grep 50511)
    if [ -z "$iptables_rules" ]; then
        echo "   [INFO] 未找到端口50511的iptables规则（可能使用默认策略）"
    else
        echo "   [INFO] 找到iptables规则:"
        echo "$iptables_rules"
    fi
else
    echo "   [SKIP] iptables未安装"
fi

# 6. 检查云服务器信息
echo ""
echo "6. 云服务器信息:"
if [ -f /sys/class/dmi/id/product_name ]; then
    product=$(cat /sys/class/dmi/id/product_name)
    echo "   服务器类型: $product"
fi

# 检查是否是阿里云
if [ -f /etc/cloud/cloud.cfg ] && grep -q "aliyun" /etc/cloud/cloud.cfg 2>/dev/null; then
    echo "   [检测到] 阿里云ECS服务器"
    echo "   [重要] 请检查阿里云控制台 -> ECS -> 安全组 -> 入站规则"
    echo "   需要添加规则: 端口50511, 协议TCP, 授权对象: 你的IP或0.0.0.0/0"
elif hostname | grep -qi "aliyun\|ali"; then
    echo "   [可能] 阿里云服务器"
    echo "   [重要] 请检查阿里云控制台 -> ECS -> 安全组 -> 入站规则"
fi

# 7. 测试本地连接
echo ""
echo "7. 测试本地数据库连接:"
if psql -h 127.0.0.1 -p 50511 -U postgres -d app -c "SELECT 1;" &>/dev/null; then
    echo "   [OK] 本地连接成功"
else
    echo "   [FAIL] 本地连接失败"
fi

# 8. 获取服务器公网IP
echo ""
echo "8. 服务器网络信息:"
public_ip=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null)
if [ -n "$public_ip" ]; then
    echo "   公网IP: $public_ip"
fi
local_ips=$(hostname -I 2>/dev/null)
if [ -n "$local_ips" ]; then
    echo "   内网IP: $local_ips"
fi

echo ""
echo "============================================================"
echo "诊断完成"
echo "============================================================"
echo ""
echo "如果所有检查都正常，但仍无法从外部连接，请检查："
echo "1. 云服务器安全组规则（阿里云/腾讯云等）"
echo "2. 网络路由和NAT配置"
echo "3. 从本地测试: Test-NetConnection -ComputerName 8.145.33.61 -Port 50511"
