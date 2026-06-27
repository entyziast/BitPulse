FROM golang:1.26-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -o rate_limiter cmd/server/main.go


FROM alpine:latest

WORKDIR /root/

COPY --from=builder /app/rate_limiter .

EXPOSE 50051

CMD ["./rate_limiter"]