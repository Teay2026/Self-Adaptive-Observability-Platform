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

## 🧪 **Tests et Validation**

### **Test Automatique Complet**
```bash
# Exécuter tous les tests de l'interface de démonstration
python test_demo_ui.py
```

### **Test Manuel des Endpoints**
```bash
# Vérifier la santé de l'interface
curl http://localhost:8081/api/health

# Obtenir le statut de tous les services
curl http://localhost:8081/api/status

# Tester la génération de charge
curl -X POST http://localhost:8081/api/load \
  -H "Content-Type: application/json" \
  -d '{"duration": 60, "concurrency": 4}'
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

## 🔧 **Configuration**

### **Variables d'Environnement**
```bash
FLASK_ENV=development  # Mode développement
```

### **Personnalisation des Services**
Modifiez `app.py` pour ajuster les URLs des services :
```python
SERVICES = {
    'go-api': 'http://localhost:8080',
    'controller': 'http://localhost:9095',
    'prometheus': 'http://localhost:9091',
    # ... autres services
}
```

## 📊 **Métriques Disponibles**

### **Requêtes Prometheus Intégrées**
- `rate(api_requests_total[1m])` : Taux de requêtes par seconde
- `rate(api_errors_total[1m]) / rate(api_requests_total[1m]) * 100` : Taux d'erreur
- `histogram_quantile(0.9, rate(api_request_duration_seconds_bucket[1m]))` : Latence P90

### **Métriques du Contrôleur**
- **Via l'API existante** : `/api/state` et `/api/rate`
- **Métriques Prometheus** : `controller_sampling_rate`, `controller_decisions_total`

## 🎯 **Cas d'Usage**

### **Démonstration Client**
1. **Démarrer la plateforme** : `make up`
2. **Ouvrir l'interface** : http://localhost:8081
3. **Expliquer l'architecture** via les statuts des services
4. **Démontrer la génération de charge**
5. **Montrer l'adaptation automatique** du contrôleur
6. **Naviguer vers Grafana** pour les visualisations

### **Test de Performance**
1. **Établir une ligne de base** avec les métriques
2. **Générer une charge progressive**
3. **Observer les adaptations automatiques**
4. **Analyser l'impact** sur les performances
5. **Vérifier la récupération automatique**

### **Développement et Debug**
1. **Utiliser l'interface** pour tester les modifications
2. **Surveiller les métriques** en temps réel
3. **Déclencher des scénarios** de test
4. **Analyser les logs** et décisions
5. **Valider les comportements** attendus

## 🔗 **Intégration avec l'Architecture Existante**

### **APIs Utilisées**
- **Controller** : `/api/state`, `/api/rate`
- **Go API** : `/control/sampling`
- **Prometheus** : `/api/v1/query`
- **Scripts** : `../scripts/loadgen.sh`

### **Flux de Données**
```
Interface Demo → Controller API → Go API → Sampling Control
Interface Demo → Prometheus API → Métriques
Interface Demo → Script loadgen.sh → Génération de charge
```

## 🚨 **Dépannage**

### **Problèmes Courants**

**Interface de démonstration inaccessible**
```bash
# Vérifier que le service est démarré
docker ps | grep demo-ui

# Vérifier les logs
docker logs <container_id>
```

**Services non détectés**
```bash
# Vérifier que tous les services sont démarrés
make up

# Vérifier les ports
netstat -tlnp | grep -E ':(8081|8080|9091|9093|9095|3000)'
```

**Erreurs de métriques**
```bash
# Vérifier Prometheus
curl http://localhost:9091/api/v1/query?query=up

# Vérifier l'API
curl http://localhost:8080/healthz
```

### **Logs et Debug**
- Les logs de l'interface s'affichent dans la console
- Utilisez la section "Logs de Démonstration" pour le debugging
- Vérifiez la console du navigateur pour les erreurs JavaScript

## 🎉 **Avantages de cette Approche**

### **1. Intégration Native**
- **Pas de duplication** de code ou de fonctionnalités
- **Utilisation des APIs existantes** du contrôleur et de l'API
- **Réutilisation des scripts** et outils existants

### **2. Architecture Cohérente**
- **Port 8081** : Évite les conflits avec AirPlay sur macOS
- **Dépendances claires** : Démarre après les services essentiels
- **Configuration unifiée** : Via Docker Compose

### **3. Maintenance Simplifiée**
- **Code minimal** : Seulement l'interface de démonstration
- **Logique métier** : Déjà implémentée dans le contrôleur
- **Tests intégrés** : Validation de tous les composants

## 🔮 **Évolutions Futures**

- **Authentification** : Intégration avec le système existant
- **Alertes personnalisées** : Via l'API du contrôleur
- **Historique des métriques** : Intégration avec Prometheus
- **Notifications push** : Via l'infrastructure existante

## 📞 **Support**

Pour toute question ou problème :
1. **Vérifiez les logs** de l'interface de démonstration
2. **Consultez la documentation** des composants existants
3. **Testez les endpoints** individuellement
4. **Vérifiez la configuration** Docker

---

## 🎯 **Résumé**

Cette interface de démonstration est **parfaitement intégrée** à votre architecture existante :

- ✅ **Utilise les APIs existantes** du contrôleur et de l'API
- ✅ **Réutilise les scripts** et outils déjà en place
- ✅ **Port 8081** : Évite les conflits avec AirPlay
- ✅ **Architecture cohérente** : Via Docker Compose
- ✅ **Tests complets** : Validation de tous les composants
- ✅ **Interface moderne** : Bootstrap + FontAwesome

**🎉 Votre plateforme d'observabilité est maintenant parfaitement démontrable avec une interface intégrée et cohérente !**
