FROM redis:7-alpine

# Expose internal port
EXPOSE 6379

# Use the environment variable to set the requirepass directive
CMD ["sh", "-c", "redis-server --requirepass $REDIS_PASSWORD"]