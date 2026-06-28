FROM node:22-alpine as builder

WORKDIR /app

# 使用 npm（项目使用 package-lock.json）
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 内联 Nginx 配置（支持 SPA history fallback + API 代理）
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
