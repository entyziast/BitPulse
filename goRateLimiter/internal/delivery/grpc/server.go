package grpc

import (
	context "context"
	"goRateLimiter/internal/domain"
)

type gRPCServer struct {
	UnimplementedRateLimiterServer
	useCase domain.RateLimiterUseCase
}

func NewGRPCServer(uc domain.RateLimiterUseCase) *gRPCServer {
	return &gRPCServer{
		useCase: uc,
	}
}

func (s *gRPCServer) CheckAccess(ctx context.Context, ip *RequestIP) (*ResponseAccess, error) {
	ok := s.useCase.CheckAccess(ctx, ip.Ip)
	return &ResponseAccess{
		Access: ok,
	}, nil
}
