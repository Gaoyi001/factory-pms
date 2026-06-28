# Docker 部署指南

## 一、概述

项目支持 Docker Compose 一键部署，包含以下服务：

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| MySQL | mysql:8.0 | 3306 | 关系型数据库 |
| Redis | redis:7-alpine | 6379 | 缓存服务 |
| MinIO | minio/minio:latest | 9000, 9001 | 对象存储 |
| Backend | 本地构建 | 8000 | FastAPI 后端 |
| Frontend | 本地构建 | 80 | Vue3 前端 + Nginx |

**配置文件**: [docker-compose.yml](file:///g:/资料/code/factory-pms/deploy/docker-compose.yml)

---

## 二、快速部署

### 2.1 准备工作

确保已安装：
- Docker Engine 20.10+
- Docker Compose v2+

### 2.2 配置环境变量

```bash
cd factory-pms/deploy

# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（重要：修改默认密码）
vim .env
```

### 2.3 启动所有服务

```bash
# 在 deploy 目录下
docker-compose up -d
```

参数说明：
- `-d`: 后台运行

### 2.4 初始化数据库

首次运行需要初始化数据库：

```bash
docker exec -it factory-pms-backend python run.py
```

### 2.5 访问应用

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost | 主入口 |
| 后端 API | http://localhost:8000/api/v1 | API 接口 |
| API 文档 | http://localhost:8000/api/v1/docs | Swagger UI |
| MinIO 控制台 | http://localhost:9001 | 对象存储管理 |

### 2.6 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | admin |

---

## 三、服务详情

### 3.1 MySQL

**配置：**
- 数据库名：`factory_pms`
- 用户名：`pms`
- 密码：`pms_secret`（请修改）
- 数据卷：`mysql_data`

**常用命令：**
```bash
# 查看日志
docker logs factory-pms-mysql

# 进入 MySQL
docker exec -it factory-pms-mysql mysql -u pms -p

# 备份数据库
docker exec factory-pms-mysql mysqldump -u pms -p factory_pms > backup.sql
```

### 3.2 Redis

**配置：**
- 数据卷：`redis_data`
- 版本：Redis 7 Alpine

**常用命令：**
```bash
# 查看日志
docker logs factory-pms-redis

# 进入 Redis CLI
docker exec -it factory-pms-redis redis-cli
```

### 3.3 MinIO

**配置：**
- API 端口：9000
- Console 端口：9001
- 访问密钥：`minioadmin`（请修改）
- 数据卷：`minio_data`

**常用命令：**
```bash
# 查看日志
docker logs factory-pms-minio

# 创建 bucket（首次）
# 登录 9001 控制台手动创建 factory-pms bucket
```

### 3.4 Backend (FastAPI)

**Dockerfile**: `backend/Dockerfile`

**配置：**
- 端口：8000
- 启动命令：`uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- 依赖于：mysql, redis, minio

**常用命令：**
```bash
# 查看日志
docker logs -f factory-pms-backend

# 进入容器
docker exec -it factory-pms-backend bash

# 重启服务
docker restart factory-pms-backend

# 重新构建
docker-compose up -d --build backend
```

### 3.5 Frontend (Vue3 + Nginx)

**Dockerfile**: `frontend/Dockerfile`

**配置：**
- 端口：80
- 基于 Nginx
- 反向代理 `/api/v1` 到 backend:8000

**常用命令：**
```bash
# 查看日志
docker logs factory-pms-frontend

# 重新构建
docker-compose up -d --build frontend
```

---

## 四、常用运维命令

### 4.1 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器 + 数据卷（危险！）
docker-compose down -v

# 重启某个服务
docker-compose restart backend

# 查看状态
docker-compose ps
```

### 4.2 日志查看

```bash
# 查看所有服务日志
docker-compose logs

# 查看指定服务日志
docker-compose logs backend

# 实时跟踪日志
docker-compose logs -f backend

# 查看最近 100 行
docker-compose logs --tail=100 backend
```

### 4.3 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 只重建后端
docker-compose up -d --build backend

# 只重建前端
docker-compose up -d --build frontend
```

---

## 五、生产环境建议

### 5.1 安全配置

- [ ] 修改所有默认密码
- [ ] 修改 JWT SECRET_KEY 为随机字符串
- [ ] 配置 HTTPS（使用 Nginx 或反向代理）
- [ ] 限制 MySQL/Redis/MinIO 端口不对外暴露
- [ ] 定期备份数据库

### 5.2 性能优化

- [ ] 增加 MySQL 连接池配置
- [ ] 配置 Redis 持久化策略
- [ ] 使用 Nginx 缓存静态资源
- [ ] 配置 gzip 压缩

### 5.3 监控

- [ ] 配置日志收集
- [ ] 添加健康检查
- [ ] 配置告警通知

---

## 六、Nginx 配置说明

**配置文件**: [nginx.conf](file:///g:/资料/code/factory-pms/deploy/nginx.conf)

前端容器内置 Nginx，主要功能：

1. **静态文件服务** - 提供前端构建产物
2. **SPA 路由支持** - try_files 支持 history 模式
3. **API 反向代理** - `/api/v1` 代理到后端
4. **gzip 压缩** - 压缩静态资源

### 自定义 Nginx 配置

如需修改 Nginx 配置：

1. 编辑 `deploy/nginx.conf`
2. 重新构建前端镜像：
```bash
docker-compose up -d --build frontend
```

---

## 七、数据备份与恢复

### 7.1 数据库备份

```bash
# 备份
docker exec factory-pms-mysql mysqldump -u pms -p'pms_secret' factory_pms > backup_$(date +%Y%m%d).sql

# 恢复
docker exec -i factory-pms-mysql mysql -u pms -p'pms_secret' factory_pms < backup.sql
```

### 7.2 MinIO 备份

```bash
# 直接备份数据卷
# 或使用 mc 客户端同步
```
