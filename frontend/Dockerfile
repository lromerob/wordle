# syntax=docker/dockerfile:1
FROM node:24-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY index.html vite.config.js ./
COPY src/ ./src/
# Public URL only; never pass credentials as build arguments.
ENV VITE_API_BASE_URL=/api
RUN npm run build

FROM nginx:1.28-alpine AS runtime
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build --chown=nginx:nginx /app/dist/ /usr/share/nginx/html/
USER nginx
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
# Bypass image entrypoint scripts; the runtime filesystem can stay read-only.
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
