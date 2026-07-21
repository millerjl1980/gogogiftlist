FROM oven/bun:1.1-alpine AS development

WORKDIR /app

COPY package.json bun.lockb* ./
RUN bun install
COPY . .

EXPOSE 3000

FROM development AS build

RUN bun run build

FROM nginx:1.27-alpine AS production

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
