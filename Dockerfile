ARG BUILD_FROM=hcr.io/hassio-addons/base:18.0.3
FROM $BUILD_FROM
ENV LANG=C.UTF-8

#Add nginx and create the run folder for nginx.
RUN apk --no-cache add tar python3; \
    ln -s /usr/bin/python3 /bin/python

COPY --from=ghcr.io/astral-sh/uv:0.5.29 /uv /uvx /bin/

ADD . /app

WORKDIR /app

RUN uv sync --frozen
RUN rm -rf /tmp/*

# ARG UID=1000
# ARG GID=1000

# RUN addgroup -g $GID pvs
# RUN adduser -D -u $UID -G pvs pvs
# USER pvs

CMD ["/app/hass_entry.sh"]
