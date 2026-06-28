package httpDelivery

import (
	"goRateLimiter/internal/domain"
	"log"
	"net"
	"net/http"
)

type HTTPHandler struct {
	usecase domain.RateLimiterUseCase
}

func NewHTTPHandler(uc domain.RateLimiterUseCase) *HTTPHandler {
	return &HTTPHandler{
		usecase: uc,
	}
}

func (h *HTTPHandler) CheckAccess(w http.ResponseWriter, r *http.Request) {
	clientIP := r.Header.Get("X-Real-IP")
	if clientIP == "" {
		host, _, err := net.SplitHostPort(r.RemoteAddr)
		if err == nil {
			clientIP = host
		} else {
			log.Printf("WARNING: Request without valid IP source received")
			w.WriteHeader(http.StatusOK)
			return
		}
	}

	allowed := h.usecase.CheckAccess(r.Context(), clientIP)
	if !allowed {
		w.WriteHeader(http.StatusTooManyRequests)
		return
	}

	w.WriteHeader(http.StatusOK)
}

func (h *HTTPHandler) PanicRecoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				log.Printf("Recovered from panic: %v", rec)
				w.WriteHeader(http.StatusOK)
			}
		}()
		next.ServeHTTP(w, r)

	})
}
