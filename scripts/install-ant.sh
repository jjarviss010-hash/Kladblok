#!/usr/bin/env bash
# Installeert de Anthropic CLI (`ant`) via de Go-moduleproxy.
# GitHub-downloads zijn in de cloud-omgeving geblokkeerd; proxy.golang.org niet.
set -euo pipefail

if command -v ant >/dev/null 2>&1; then
  ant --version
  exit 0
fi

export GOTOOLCHAIN=go1.25.0+auto
go install github.com/anthropics/anthropic-cli/cmd/ant@latest
echo "Geïnstalleerd: $(go env GOPATH)/bin/ant"
echo "Zet in je PATH: export PATH=\$PATH:$(go env GOPATH)/bin"
"$(go env GOPATH)/bin/ant" --version
