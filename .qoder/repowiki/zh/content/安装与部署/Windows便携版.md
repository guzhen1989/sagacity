# Windows便携版

<cite>
**本文档引用的文件**   
- [portable-installation-guide.md](file://docs/guides/portable-installation-guide.md)
- [portable-port-configuration.md](file://docs/deployment/portable-port-configuration.md)
- [portable-python-independence.md](file://docs/deployment/portable-python-independence.md)
- [start_all.ps1](file://scripts/installer/start_all.ps1)
- [stop_all.ps1](file://scripts/installer/stop_all.ps1)
- [setup_embedded_python.ps1](file://scripts/deployment/setup_embedded_python.ps1)
- [build_portable_package.ps1](file://scripts/deployment/build_portable_package.ps1)
- [data-directory-configuration.md](file://docs/configuration/data-directory-configuration.md)
</cite>

## 目录
1. [简介](#简介)
2. [系统要求](#系统要求)
3. [下载与解压](#下载与解压)
4. [初始化配置](#初始化配置)
5. [目录结构与数据存储](#目录结构与数据存储)
6. [启动与停止服务](#启动与停止服务)
7. [端口配置](#端口配置)
8. [数据目录迁移与备份恢复](#数据目录迁移与备份恢复)
9. [更新流程与版本升级](#更新流程与版本升级)
10. [配置为Windows服务](#配置为windows服务)
11. [防火墙与杀毒软件兼容性](#防火墙与杀毒软件兼容性)
12. [常见问题解决](#常见问题解决)

## 简介

sagacity系统的Windows便携版是一个免安装、开箱即用的部署方案，所有依赖（包括Python、MongoDB、Redis、Nginx等）均已打包，无需复杂的环境配置即可快速部署和使用。该版本具有便携性、隔离性和一键启动等特点，适合在U盘或移动硬盘中运行，且不会影响系统环境。

**Section sources**
- [portable-installation-guide.md](file://docs/guides/portable-installation-guide.md#简介)

## 系统要求

### 最低配置
- **操作系统**：Windows 10/11 (64位)
- **CPU**：双核处理器
- **内存**：4GB RAM
- **磁盘空间**：5GB 可用空间
- **网络**：需要联网访问数据源 API

### 推荐配置
- **操作系统**：Windows 10/11 (64位)
- **CPU**：四核或更高
- **内存**：8GB RAM 或更高
- **磁盘空间**：10GB 可用空间
- **网络**：稳定的网络连接

**Section sources**
- [portable-installation-guide.md](file://docs/guides/portable-installation-guide.md#系统要求)

## 下载与解压

1. 下载 `TradingAgentsCN-Portable-vX.X.X.zip` 或 `.7z` 安装包。
2. 解压到任意目录（建议路径不包含中文和空格），例如：`D:\TradingAgentsCN-portable`。
3. 确保解压后的目录结构完整，包含 `start_all.ps1`、`.env` 等关键文件。

**Section sources**
- [portable-installation-guide.md](file://docs/guides/portable-installation-guide.md#第一步解压安装包)

## 初始化配置

1. 以**管理员身份**运行 PowerShell。
2. 进入安装目录：
   ```powershell
   cd D:\TradingAgentsCN-portable
   ```
3. 运行初始化脚本：
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\installer\setup.ps1
   ```
4. 初始化脚本会自动检查环境、创建目录、初始化数据库、配置缓存和服务器，并安装Python依赖包。

**Section sources**
- [portable-installation-guide.md](file://docs/guides/portable-installation-guide.md#第二步初始化环境)

## 目录结构与数据存储

解压后的便携版目录结构如下：
```
TradingAgentsCN-portable/
├── app/                    # 后端应用代码
├── tradingagents/          # 核心库代码
├── web/                    # 前端代码
├── vendors/                # 第三方依赖
│   ├── mongodb/            # MongoDB 数据库
│   ├── redis/              # Redis 缓存
│   ├── nginx/              # Nginx 服务器
│   └── python/             # Python 环境
├── data/                   # 数据目录
│   ├── mongodb/            # MongoDB 数据文件
│   ├── redis/              # Redis 数据文件
│   └── cache/              # 缓存文件
├── logs/                   # 日志目录
├── config/                 # 配置文件
├── scripts/                # 脚本目录
│   └── installer/          # 安装和启动脚本
├── .env                    # 环境变量配置
└── README.md               # 说明文档
```

数据存储位置可通过环境变量或CLI命令自定义，优先级为：环境变量 > CLI设置 > 默认配置。默认路径为 `C:\Users\{username}\Documents\TradingAgents\data`。

**Section sources**
- [portable-installation-guide.md](file://docs/guides/portable-installation-guide.md#第一步解压安装包)
- [data-directory-configuration.md](file://docs/configuration/data-directory-configuration.md#目录结构)

## 启动与停止服务

### 启动服务
- 双击运行 `start_all.ps1`，或在PowerShell中执行：
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\start_all.ps1
  ```
- 首次启动会自动导入配置并创建默认管理员账号（admin/admin123）。

### 停止服务
- 双击运行 `stop_all.ps1`，或在PowerShell中执行：
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\stop_all.ps1
  ```
- 停止顺序为：Nginx → Backend → Redis → MongoDB，确保数据正确保存。

**Section sources**
- [portable-installation-guide.md](file://docs/guides/portable-installation-guide.md#第四步启动服务)
- [stop_all.ps1](file://scripts/installer/stop_all.ps1)

## 端口配置

便携版默认使用以下端口：
- **前端 (Nginx)**：80
- **后端 (FastAPI)**：8000
- **MongoDB**：27017
- **Redis**：6379

修改端口需编辑相应配置文件：
- **Nginx**：修改 `runtime/nginx.conf` 中的 `listen` 和 `upstream backend` 端口。
- **FastAPI**：修改 `.env` 文件中的 `PORT`。
- **MongoDB**：修改 `scripts/installer/start_services_clean.ps1` 中的 `--port` 参数。
- **Redis**：修改 `runtime/redis.conf` 中的 `port`。

修改后需重启服务生效。

**Section sources**
- [portable-port-configuration.md](file://docs/deployment/portable-port-configuration.md#概述)

## 数据目录迁移与备份恢复

### 数据目录迁移
通过环境变量或CLI命令设置新的数据目录：
```bash
# Windows
set TRADINGAGENTS_DATA_DIR=C:\MyTradingData

# Linux/macOS
export TRADINGAGENTS_DATA_DIR="/home/user/trading-data"
```

### 备份与恢复
- **备份**：运行 `backup_mongodb.ps1` 脚本。
- **恢复**：运行 `restore_mongodb.ps1` 脚本并指定备份文件。

**Section sources**
- [data-directory-configuration.md](file://docs/configuration/data-directory-configuration.md#配置方法)
- [portable-installation-guide.md](file://docs/guides/portable-installation-guide.md#数据备份)

## 更新流程与版本升级

1. 备份当前数据：
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\maintenance\backup_mongodb.ps1
   ```
2. 停止所有服务：
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\installer\stop_all.ps1
   ```
3. 下载新版本安装包并解压到新目录。
4. 复制旧版本的 `.env` 文件到新目录。
5. 恢复数据库备份（如需要）。
6. 启动新版本服务。

**Section sources**
- [portable-installation-guide.md](file://docs/guides/portable-installation-guide.md#如何更新到新版本)

## 配置为Windows服务

便携版暂未提供直接配置为Windows服务的功能，但可通过第三方工具（如NSSM）将 `start_all.ps1` 脚本注册为服务。建议在生产环境中使用Docker部署以获得更好的服务管理能力。

**Section sources**
- [portable-installation-guide.md](file://docs/guides/portable-installation-guide.md)

## 防火墙与杀毒软件兼容性

- **防火墙**：确保允许便携版使用的端口（80, 8000, 27017, 6379）通过防火墙。
- **杀毒软件**：将便携版目录添加到杀毒软件白名单，避免误杀关键进程（如 `mongod.exe`, `redis-server.exe`, `nginx.exe`）。

**Section sources**
- [portable-installation-guide.md](file://docs/guides/portable-installation-guide.md)

## 常见问题解决

### Q1: 启动失败，提示端口被占用
- 检查占用端口的进程并关闭，或修改 `.env` 文件中的端口配置。

### Q2: 无法访问前端页面
- 检查Nginx是否启动，查看 `logs/nginx_error.log` 错误日志。

### Q3: 数据同步失败
- 检查API密钥配置和网络连接，查看 `logs/api.log` 日志。

### Q4: AI分析功能无法使用
- 检查LLM API密钥配置和网络连接。

### Q5: MongoDB启动失败
- 检查 `logs/mongodb.log` 日志，尝试删除 `data\mongodb\db\mongod.lock` 文件后重启。

**Section sources**
- [portable-installation-guide.md](file://docs/guides/portable-installation-guide.md#常见问题)