package main

import (
	"context"
	"goRateLimiter/internal/delivery/grpc"
	"goRateLimiter/internal/domain"
	"goRateLimiter/internal/repository"
	"goRateLimiter/internal/usecase"
	"log"
	"net"
	"os"
	"strconv"
	"time"

	"github.com/joho/godotenv"
	"github.com/redis/go-redis/v9"
	googleGrpc "google.golang.org/grpc"
)

func main() {
	listener, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("Error open tcp port :50051 %s", err)
	}

	_ = godotenv.Load(".env")
	_ = godotenv.Load("../.env")

	redis_url := os.Getenv("REDIS_URL_RATELIMITER")
	if redis_url == "" {
		redis_url = "localhost:6379"
	}

	client := redis.NewClient(
		&redis.Options{
			Addr:     redis_url,
			DB:       0,
			PoolSize: 300,
		},
	)

	// test connection to Redis
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	err = client.Ping(ctx).Err()
	if err != nil {
		log.Fatalf("RateLimiter failed to connect to Redis at %s: %v", client.Options().Addr, err)
	}
	log.Println("RateLimiter successfully connected to Redis.")

	var TokensPerSecond, BucketCapacity float64
	var errParseTPS, errParseBC error

	TokensPerSecond, errParseTPS = strconv.ParseFloat(os.Getenv("TOKENS_PER_SECOND"), 64)
	BucketCapacity, errParseBC = strconv.ParseFloat(os.Getenv("BUCKET_CAPACITY"), 64)
	if errParseTPS != nil || errParseBC != nil || TokensPerSecond == 0 || BucketCapacity == 0 {
		log.Println(domain.ErrNotFoundConfigData)
		TokensPerSecond = 1
		BucketCapacity = 10
	}

	config := domain.RateLimiterConfig{
		TokensPerSecond: TokensPerSecond,
		BucketCapacity:  BucketCapacity,
	}
	repo := repository.NewRedisRepository(client, config)
	useCase := usecase.NewLimiterUseCase(repo, config)
	grpcHandler := grpc.NewGRPCServer(useCase)

	grpcServer := googleGrpc.NewServer()
	grpc.RegisterRateLimiterServer(grpcServer, grpcHandler)
	log.Println("gRPC server started...")

	if err := grpcServer.Serve(listener); err != nil {
		log.Fatal(err)
	}
}
