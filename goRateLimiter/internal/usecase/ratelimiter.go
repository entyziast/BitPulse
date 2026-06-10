package usecase

import (
	"context"
	"fmt"
	"goRateLimiter/internal/domain"
	"time"
)

type LimiterUseCase struct {
	repo   domain.RateLimiterRepository
	config domain.RateLimiterConfig
}

func NewLimiterUseCase(repo domain.RateLimiterRepository, config domain.RateLimiterConfig) domain.RateLimiterUseCase {
	return &LimiterUseCase{
		repo:   repo,
		config: config,
	}
}

func (uc LimiterUseCase) CheckAccess(ctx context.Context, ip string) bool {
	oldStatus, err := uc.repo.GetCurrentTokens(ctx, ip)
	var curTokens float64
	if err == domain.ErrIPNotFound {
		curTokens = uc.config.BucketCapacity
	} else if err != nil {
		fmt.Printf("Error in repo.GetCurrentTokens to ip:%s: %v\n", ip, err)
		return false
	} else {
		oldTokens := oldStatus.Tokens
		lastUpdate := oldStatus.UpdatedAt

		elapsedTime := time.Since(lastUpdate)
		curTokens = oldTokens + elapsedTime.Seconds()*uc.config.TokensPerSecond
		if curTokens > uc.config.BucketCapacity {
			curTokens = uc.config.BucketCapacity
		}
	}

	if curTokens < 1 {
		return false
	}
	err = uc.repo.UpdateCurrentTokens(ctx, ip, domain.LimiterStatus{Tokens: curTokens - 1, UpdatedAt: time.Now()})
	if err != nil {
		fmt.Println("error in UpdateCurrentTokens:", err)
	}
	return true
}
