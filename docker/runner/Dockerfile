FROM ubuntu:24.04@sha256:9c7f200c07e3d4a03e7249d2c16bf66a51120fb876aa2242cf31451412543289
SHELL ["/bin/bash", "-euo", "pipefail", "-c"]
ARG DEBIAN_FRONTEND=noninteractive
# Signed Ubuntu and Microsoft package repositories; no curl-pipe-shell installers.
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git python3 python3-venv unzip xz-utils jq gnupg tini libicu74 libssl3t64 libkrb5-3 zlib1g liblttng-ust1t64 libcurl4t64 && rm -rf /var/lib/apt/lists/*
RUN curl --fail --silent --show-error https://packages.microsoft.com/keys/microsoft.asc -o /tmp/microsoft.asc &&     gpg --show-keys --with-colons /tmp/microsoft.asc | grep -q 'BC528686B50D79E339D3721CEB3E94ADBE1229CF' &&     gpg --dearmor -o /usr/share/keyrings/microsoft-azure-cli.gpg /tmp/microsoft.asc &&     echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-azure-cli.gpg] https://packages.microsoft.com/repos/azure-cli/ noble main' > /etc/apt/sources.list.d/azure-cli.list &&     apt-get update && apt-get install -y --no-install-recommends azure-cli=2.86.0-1~noble &&     rm -rf /var/lib/apt/lists/* /tmp/microsoft.asc
COPY install_tools.py /tmp/install_tools.py
RUN python3 /tmp/install_tools.py && chown -R 10001:10001 /home/runner && rm /tmp/install_tools.py && ln -s /usr/bin/python3 /usr/local/bin/python
ENV PATH="/opt/node/bin:${PATH}" PLAYWRIGHT_BROWSERS_PATH=/opt/wordle-browser/cache
RUN mkdir -p /opt/wordle-browser && cd /opt/wordle-browser &&     npm install --registry=https://registry.npmjs.org --ignore-scripts --save-exact playwright@1.62.1 &&     ./node_modules/.bin/playwright install --with-deps --only-shell chromium &&     ln -s "$(find /opt/wordle-browser/cache -type f -name chrome-headless-shell | head -n 1)" /opt/wordle-browser/chromium &&     test -x /opt/wordle-browser/chromium && chmod -R a+rX /opt/wordle-browser &&     npm cache clean --force && rm -rf /var/lib/apt/lists/*
RUN useradd --uid 10001 --create-home --shell /bin/bash runner &&     mkdir -p /home/runner/_work && chown runner:runner /home/runner/_work
COPY --chmod=755 entrypoint.py /opt/wordle-runner/entrypoint.py
COPY --from=store_contract private_store.py /opt/wordle-runner/private_store.py
ENV WORDLE_PLAYWRIGHT_ROOT=/opt/wordle-browser/node_modules     WORDLE_BROWSER_EXECUTABLE=/opt/wordle-browser/chromium     WORDLE_AZURE_PRIVATE_DIR=/wordle-private     AZURE_CORE_COLLECT_TELEMETRY=no AZURE_LOGGING_ENABLE_LOG_FILE=no     PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 10001:10001
WORKDIR /home/runner/actions
ENTRYPOINT ["/usr/bin/tini", "-g", "--", "python3", "/opt/wordle-runner/entrypoint.py"]
CMD ["validate"]
