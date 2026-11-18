ARG BUILD_FROM=ghcr.io/hassio-addons/base:21.0.11
FROM $BUILD_FROM
ENV LANG=C.UTF-8

RUN apk --no-cache add tar python3; \
    ln -s /usr/bin/python3 /bin/python

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

# Always use the base image's Python rather than letting uv download one to match .python-version
ENV UV_PYTHON=/usr/bin/python3 \
    UV_PYTHON_DOWNLOADS=never

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
