FROM node:18-alpine AS builder

WORKDIR /app

COPY apps/web/package*.json ./

RUN npm ci

COPY apps/web .

RUN npm run build

FROM node:18-alpine

WORKDIR /app

COPY apps/web/package*.json ./

RUN npm ci --only=production

COPY --from=builder /app/dist ./dist

RUN npm install -g serve

EXPOSE 3001

CMD ["serve", "-s", "dist", "-l", "3001"]
