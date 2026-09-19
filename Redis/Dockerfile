
FROM redis:7-alpine

COPY entrypoint.sh /usr/local/bin/redis-secret-entrypoint
RUN chmod +x /usr/local/bin/redis-secret-entrypoint

EXPOSE 6379

ENTRYPOINT ["/usr/local/bin/redis-secret-entrypoint"]