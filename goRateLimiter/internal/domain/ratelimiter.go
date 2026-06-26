package domain

import (
	"context"
	"errors"
	"time"
)

var ErrIPNotFound = errors.New("data about limiter status for this ip not found")
var ErrNotFoundConfigData = errors.New("Not found TokensPerSecond and BucketCapacity in .env file, load default config")

type RateLimiterConfig struct {
	TokensPerSecond float64
	BucketCapacity  float64
}

type LimiterStatus struct {
	Tokens    float64
	UpdatedAt time.Time
}

type RateLimiterRepository interface {
	GetCurrentTokens(ctx context.Context, ip string) (LimiterStatus, error)
	UpdateCurrentTokens(ctx context.Context, ip string, status LimiterStatus) error
}

type RateLimiterUseCase interface {
	CheckAccess(ctx context.Context, ip string) bool
}
