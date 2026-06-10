package main

import (
	"goRateLimiter/internal/delivery/grpc"
	"goRateLimiter/internal/domain"
	"goRateLimiter/internal/repository"
	"goRateLimiter/internal/usecase"
	"log"
	"net"

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

	config := domain.RateLimiterConfig{
		TokensPerSecond: 1,
		BucketCapacity:  10,
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
