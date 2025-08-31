# Interface de Démonstration - Plateforme d'Observabilité Auto-Adaptative

## 🎯 **Objectif**

Cette interface de démonstration s'intègre **parfaitement** avec l'architecture existante de votre plateforme d'observabilité. Elle utilise les **endpoints déjà disponibles** dans le contrôleur et l'API, sans créer de redondance.

## 🏗️ **Architecture Intégrée**

### **Composants Existants Utilisés :**
- **Controller** (`localhost:9095`) : Interface principale avec UI intégrée
- **Go API** (`localhost:8080`) : Endpoints de contrôle et métriques
- **Prometheus** (`localhost:9091`) : Requêtes de métriques
- **Vector** (`localhost:9090`) : Collecte de logs et métriques
- **Grafana** (`localhost:3000`) : Visualisations
- **Alertmanager** (`localhost:9093`) : Gestion des alertes

### **Interface de Démonstration :**
- **Port 8081** : Évite les conflits avec AirPlay sur macOS
- **Intégration native** : Utilise les APIs existantes
- **Pas de duplication** : Complète l'interface du contrôleur

## 🚀 **Fonctionnalités**

### **1. Tableau de Bord Unifié**
- **Métriques en temps réel** : Requêtes/s, erreurs, latence, échantillonnage
- **Statut des services** : Monitoring de tous les composants
- **Mise à jour automatique** : Rafraîchissement toutes les 5 secondes

### **2. Actions de Démonstration**
- **Génération de charge** : Utilise le script `loadgen.sh` existant
- **Contrôle d'échantillonnage** : Interface avec l'API Go
- **Actions du contrôleur** : Bump/Decay via l'API du contrôleur

### **3. Intégration Native**
- **APIs existantes** : Pas de réinvention, utilisation des endpoints disponibles
- **Scripts existants** : Réutilisation de `loadgen.sh`
- **Métriques existantes** : Requêtes Prometheus standard

## 🛠️ **Installation et Démarrage**

### **Option 1 : Docker Compose (Recommandé)**
```bash
# Démarrer toute la plateforme
make up

# L'interface de démonstration sera accessible sur http://localhost:8081
```

### **Option 2 : Démarrage Local**
```bash
# Installer les dépendances
cd demo-ui
pip install -r requirements.txt

# Démarrer l'interface de démonstration
python app.py

# L'interface sera accessible sur http://localhost:8081
```

### **Option 3 : Docker Individuel**
```bash
# Construire et démarrer uniquement l'interface de démonstration
cd demo-ui
docker build -t observability-demo-ui .
docker run -p 8081:8081 observability-demo-ui
```

## 📱 **Utilisation de l'Interface**

### **1. Vérification du Statut**
- Ouvrez http://localhost:8081
- Vérifiez que tous les services sont "healthy" (vert)
- Les métriques principales s'affichent automatiquement

### **2. Démonstration de Charge**
- Dans la section "Actions de Démonstration"
- Définissez la durée (10-300 secondes)
- Définissez la concurrence (1-20 connexions)
- Cliquez sur "Démarrer la Charge"
- Observez l'impact sur les métriques

### **3. Contrôle d'Échantillonnage**
- Utilisez le slider pour modifier le taux (0.1 à 1.0)
- Cliquez sur "Appliquer"
- Observez les changements en temps réel

### **4. Actions du Contrôleur**
- Cliquez sur "Rafraîchir" pour voir l'état actuel
- Utilisez "Augmenter le Taux" ou "Diminuer le Taux"
- Observez les adaptations automatiques

### **5. Navigation vers les Outils**
- **Grafana** : Dashboards et visualisations
- **Prometheus** : Requêtes et métriques
- **Contrôleur** : Interface principale du contrôleur
- **Alertmanager** : Gestion des alertes


## 📊 **Métriques Disponibles**

### **Requêtes Prometheus Intégrées**
- `rate(api_requests_total[1m])` : Taux de requêtes par seconde
- `rate(api_errors_total[1m]) / rate(api_requests_total[1m]) * 100` : Taux d'erreur
- `histogram_quantile(0.9, rate(api_request_duration_seconds_bucket[1m]))` : Latence P90

### **Métriques du Contrôleur**
- **Via l'API existante** : `/api/state` et `/api/rate`
- **Métriques Prometheus** : `controller_sampling_rate`, `controller_decisions_total`

