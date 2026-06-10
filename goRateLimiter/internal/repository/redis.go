package repository

import (
	"context"
	"errors"
	"fmt"
	"goRateLimiter/internal/domain"
	"strconv"
	"time"

	"github.com/redis/go-redis/v9"
)

var ErrCorruptedRedisKey error = errors.New("Key rate_limit:<ip> corrupted, not found tokens or timestamp, or corrupted values")

type RedisRepository struct {
	redis  *redis.Client
	config domain.RateLimiterConfig
}

func NewRedisRepository(client *redis.Client, config domain.RateLimiterConfig) domain.RateLimiterRepository {
	return &RedisRepository{
		redis:  client,
		config: config,
	}
}

func (r RedisRepository) GetCurrentTokens(ctx context.Context, ip string) (domain.LimiterStatus, error) {

	statusMap, err := r.redis.HGetAll(ctx, fmt.Sprintf("rate_limit:%s", ip)).Result()
	if err != nil {
		return domain.LimiterStatus{}, err
	}
	if len(statusMap) == 0 {
		return domain.LimiterStatus{}, domain.ErrIPNotFound
	}

	tokensString, okToken := statusMap["tokens"]
	updatedAtString, okUpdatedAt := statusMap["timestamp"]

	if !okToken || !okUpdatedAt {
		return domain.LimiterStatus{}, ErrCorruptedRedisKey
	}

	tokens, err := strconv.ParseFloat(tokensString, 64)
	if err != nil {
		return domain.LimiterStatus{}, ErrCorruptedRedisKey
	}
	updatedAt, err := time.Parse(time.RFC3339, updatedAtString)
	return domain.LimiterStatus{
		Tokens:    tokens,
		UpdatedAt: updatedAt,
	}, nil

}

func (r RedisRepository) UpdateCurrentTokens(ctx context.Context, ip string, status domain.LimiterStatus) error {
	key := fmt.Sprintf("rate_limit:%s", ip)
	err := r.redis.HSet(ctx, key, "tokens", status.Tokens, "timestamp", status.UpdatedAt.Format(time.RFC3339)).Err()
	if err != nil {
		return err
	}
	ttl := r.config.BucketCapacity / r.config.TokensPerSecond
	err = r.redis.Expire(ctx, key, time.Duration(ttl)*time.Second).Err()
	if err != nil {
		return err
	}
	return nil
}
