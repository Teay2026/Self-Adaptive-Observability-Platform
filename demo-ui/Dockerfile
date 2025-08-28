FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Rendre le script loadgen.sh exécutable
RUN chmod +x /app/scripts/loadgen.sh

# Exposer le port 8081
EXPOSE 8081

# Commande de démarrage
CMD ["python", "app.py"]
