FROM ubuntu:20.10

RUN apt-get update \
 && apt-get install \
      -y \
      --no-install-recommends \
      apt-transport-https \
      ca-certificates \
      curl \
      gnupg \
      lsb-release \
      make \
      python3 \
      python3-pip \
      python3-venv \
      software-properties-common \
 # Install Azure CLI
 && curl -sL https://packages.microsoft.com/keys/microsoft.asc | \
      gpg --dearmor | \
      tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null \
 && AZ_REPO=$(lsb_release -cs) \
 && echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $AZ_REPO main" | \
      tee /etc/apt/sources.list.d/azure-cli.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      azure-cli

RUN python3 -m venv /venv \
 && /venv/bin/pip install \
      ansible \
      flit
