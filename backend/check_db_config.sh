#!/bin/bash
# 数据库配置检查脚本
# 在服务器上运行此脚本来检查PostgreSQL配置

echo "============================================================"
echo "PostgreSQL 配置检查"
echo "============================================================"

# 检查PostgreSQL版本
echo ""
echo "1. PostgreSQL 版本信息:"
psql -h 127.0.0.1 -p 50511 -U postgres -d app -c "SELECT version();"

# 检查监听地址
echo ""
echo "2. 检查监听地址配置:"
sudo grep -E "^listen_addresses|^#listen_addresses" /etc/postgresql/*/main/postgresql.conf 2>/dev/null || \
sudo grep -E "^listen_addresses|^#listen_addresses" /var/lib/pgsql/*/data/postgresql.conf 2>/dev/null || \
echo "请手动检查 postgresql.conf 中的 listen_addresses 设置"

# 检查pg_hba.conf配置
echo ""
echo "3. 检查客户端认证配置 (pg_hba.conf):"
sudo grep -v "^#" /etc/postgresql/*/main/pg_hba.conf 2>/dev/null | grep -v "^$" || \
sudo grep -v "^#" /var/lib/pgsql/*/data/pg_hba.conf 2>/dev/null | grep -v "^$" || \
echo "请手动检查 pg_hba.conf 文件"

# 检查端口监听状态
echo ""
echo "4. 检查端口监听状态:"
sudo netstat -tlnp | grep 50511 || sudo ss -tlnp | grep 50511

# 检查防火墙状态
echo ""
echo "5. 检查防火墙状态:"
if command -v ufw &> /dev/null; then
    echo "UFW 防火墙状态:"
    sudo ufw status | grep 50511 || echo "端口50511未在UFW规则中"
elif command -v firewall-cmd &> /dev/null; then
    echo "Firewalld 防火墙状态:"
    sudo firewall-cmd --list-ports | grep 50511 || echo "端口50511未在防火墙规则中"
elif command -v iptables &> /dev/null; then
    echo "iptables 规则:"
    sudo iptables -L -n | grep 50511 || echo "端口50511未在iptables规则中"
else
    echo "未检测到常见的防火墙工具"
fi

# 检查数据库连接数
echo ""
echo "6. 检查当前数据库连接:"
psql -h 127.0.0.1 -p 50511 -U postgres -d app -c "SELECT count(*) as current_connections, max_conn as max_connections FROM pg_stat_activity, (SELECT setting::int as max_conn FROM pg_settings WHERE name = 'max_connections') mc;"

echo ""
echo "============================================================"
echo "检查完成"
echo "============================================================"
