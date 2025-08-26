# -------- Étape 1 : build (compile le binaire Go) --------
FROM golang:1.22 AS builder

# BuildKit exposes target OS/ARCH so we build for the right platform
ARG TARGETOS
ARG TARGETARCH

WORKDIR /src

# Copier les fichiers de modules d'abord (cache des deps)
COPY go.mod go.sum ./
RUN go mod download

# Copier le code ensuite
COPY . .

# Compiler un binaire statique pour la plateforme cible
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -trimpath -ldflags="-s -w" -o /out/go-api ./main.go

# -------- Étape 2 : runtime (image minimale, sans toolchain) --------
FROM gcr.io/distroless/base-debian12
WORKDIR /

# Copier uniquement le binaire (pas le code source, pas le toolchain)
COPY --from=builder /out/go-api /go-api

# Exposer le port HTTP de l'API (info documentaire)
EXPOSE 8080

# Run as nonroot and set OCI labels
USER nonroot:nonroot
LABEL org.opencontainers.image.title="go-api" \
      org.opencontainers.image.source="https://example.local/self-adaptive-observability" \
      org.opencontainers.image.description="Demo Go API for self-adaptive observability"

# Lancer le binaire quand le conteneur démarre
ENTRYPOINT ["/go-api"]
