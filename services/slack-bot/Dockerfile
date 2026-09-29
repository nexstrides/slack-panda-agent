FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY services/slack-bot/go.mod .
COPY services/slack-bot/go.sum* .

RUN go mod download || true

COPY services/slack-bot/main.go .

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o slack-bot .

FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /app/slack-bot .

EXPOSE 3000

CMD ["./slack-bot"]
