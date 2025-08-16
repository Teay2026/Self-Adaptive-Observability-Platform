# -------- Étape 1 : build (compile le binaire Go) --------
    FROM golang:1.22 AS builder
    WORKDIR /src
    
    # Copier les fichiers de modules d'abord (cache des deps)
    COPY go.mod go.sum ./
    RUN go mod download
    
    # Copier le code ensuite
    COPY . .
    
    # Compiler un binaire statique Linux (on tourne des conteneurs Linux sur Mac)
    RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/go-api ./main.go
    
    # -------- Étape 2 : runtime (image minimale, sans toolchain) --------
    FROM gcr.io/distroless/base-debian12
    WORKDIR /
    
    # Copier uniquement le binaire (pas le code source, pas le toolchain)
    COPY --from=builder /out/go-api /go-api
    
    # Exposer le port HTTP de l'API (info documentaire)
    EXPOSE 8080
    
    # Lancer le binaire quand le conteneur démarre
    ENTRYPOINT ["/go-api"]
    