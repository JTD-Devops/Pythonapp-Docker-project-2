FROM mysql:8.0

ENV MYSQL_ROOT_PASSWORD=rootpass
ENV MYSQL_DATABASE=novels_db
ENV MYSQL_USER=novels_user
ENV MYSQL_PASSWORD=novels_pass

COPY database.sql /docker-entrypoint-initdb.d/

EXPOSE 3306

CMD ["mysqld", "--character-set-server=utf8mb4", "--collation-server=utf8mb4_unicode_ci"]
