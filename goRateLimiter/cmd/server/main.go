package main

import (
	"goRateLimiter/internal/delivery/grpc"
	"goRateLimiter/internal/domain"
	"goRateLimiter/internal/repository"
	"goRateLimiter/internal/usecase"
	"log"
	"net"
	"os"
	"strconv"

	"github.com/joho/godotenv"
	"github.com/redis/go-redis/v9"
	googleGrpc "google.golang.org/grpc"
)

func main() {
	listener, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("Error open tcp port :50051 %s", err)
	}

	client := redis.NewClient(
		&redis.Options{
			Addr:     "localhost:6379",
			DB:       0,
			PoolSize: 10,
		},
	)

	err1 := godotenv.Load(".env")
	err2 := godotenv.Load("../.env") // для запуска через `go run cmd/server/main.go`
	var TokensPerSecond, BucketCapacity float64
	if err1 != nil && err2 != nil {
		log.Println(domain.ErrNotFoundConfigData)
		TokensPerSecond = 1
		BucketCapacity = 10
	} else {
		var errParseTPS, errParseBC error
		TokensPerSecond, errParseTPS = strconv.ParseFloat(os.Getenv("TOKENS_PER_SECOND"), 64)
		BucketCapacity, errParseBC = strconv.ParseFloat(os.Getenv("BUCKET_CAPACITY"), 64)
		if errParseBC != nil || errParseTPS != nil {
			log.Println(domain.ErrNotFoundConfigData)
			TokensPerSecond = 1
			BucketCapacity = 10
		}
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
