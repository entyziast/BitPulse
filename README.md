
# refresh token

в Redis даннные храняться так: 
refresh:{username} - refresh_token
search:{query}:limit:{limit} - value
tg_secret_token:{secret_token} - chat_id
rate_limiter:{ip_adress} - {tokens: {кол-во доступных токенов}, timestamp: {время последнего обновления}}