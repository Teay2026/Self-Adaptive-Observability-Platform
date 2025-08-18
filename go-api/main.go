package main

// import = on amène d'autres packages pour pouvoir utiliser leurs fonctions
import (
	"encoding/json" // pour encoder nos logs en JSON
	"fmt"           // pour afficher du texte (ex: fmt.Println)
	"log"           // pour afficher des logs côté console
	"math/rand"     // pour générer des nombres aléatoires (simuler des erreurs)
	"net"           // pour gérer les connexions réseau (TCP ici)
	"net/http"      // pour créer notre serveur HTTP
	"os"            // pour lire les variables d'environnement
	"strconv"

	// pour parser le taux depuis la query string
	"sync/atomic" // pour stocker le taux de sampling de manière thread-safe
	"time"        // pour mesurer le temps d'exécution et ajouter des horodatages

	// Prometheus client
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"

	// Package externe : client DogStatsD en Go
	"gopkg.in/alexcesaro/statsd.v2"
)

// On définit un "type" LogEvent pour représenter la structure de nos logs JSON.
// Les tags entre `...` disent comment nommer chaque champ dans le JSON.
type LogEvent struct {
	Service string  `json:"service"`
	Env     string  `json:"env"`
	Level   string  `json:"level"`
	Msg     string  `json:"msg"`
	Path    string  `json:"path"`
	Status  int     `json:"status"`
	Latency float64 `json:"latency_ms"`
	Time    string  `json:"time"`
}

var (
	promRequests = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "api_requests_total",
		Help: "Total HTTP requests",
	})
	promErrors = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "api_errors_total",
		Help: "Total HTTP 5xx errors",
	})
	promLatency = prometheus.NewHistogram(prometheus.HistogramOpts{
		Name:    "api_request_duration_seconds",
		Help:    "Request duration seconds",
		Buckets: prometheus.DefBuckets,
	})
)

var sampleRate atomic.Value // float64 in [0,1]

func main() {
	// ============================
	// 1) Lire la config via les variables d'environnement
	// ============================
	statsdAddr := getenv("STATSD_ADDR", "vector:8125") // UDP DogStatsD vers Vector
	logAddr := getenv("LOG_TARGET", "vector:9000")     // TCP logs vers Vector
	service := getenv("SERVICE_NAME", "api")
	env := getenv("ENV", "dev")

	// Taux de sampling initial (1.0 = pas de sampling)
	sampleRate.Store(1.0)

	// Enregistrer les métriques Prometheus
	prometheus.MustRegister(promRequests, promErrors, promLatency)

	// ============================
	// 2) Connexion UDP au client DogStatsD
	// ============================
	c, err := statsd.New(
		statsd.Address(statsdAddr),                  // où envoyer
		statsd.Prefix("api_"),                       // préfixe Prometheus-friendly
		statsd.TagsFormat(statsd.Datadog),           // format de tags DogStatsD
		statsd.Tags("service:"+service, "env:"+env), // ✅ liste de "clé:valeur"
	)
	if err != nil {
		log.Fatalf("statsd init failed: %v", err)
	}
	defer c.Close()

	// ============================
	// 3) Connexion TCP à Vector pour logs
	// ============================
	conn, err := net.Dial("tcp", logAddr)
	if err != nil {
		log.Fatalf("log tcp connect failed: %v", err)
	}
	defer conn.Close()

	// ============================
	// 4) Serveur HTTP
	// ============================
	mux := http.NewServeMux()
	// Exposer /metrics pour Prometheus
	mux.Handle("/metrics", promhttp.Handler())

	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Simuler un traitement
		time.Sleep(time.Duration(rand.Intn(100)) * time.Millisecond)

		status := 200
		if rand.Float32() < 0.10 { // 10% d'erreurs simulées
			status = 500
			http.Error(w, "error", http.StatusInternalServerError)
		} else {
			fmt.Fprintln(w, "ok")
		}

		// Latence
		latency := time.Since(start)
		latencyMs := float64(latency.Milliseconds())

		// Prometheus metrics (toujours)
		promRequests.Inc()
		promLatency.Observe(latency.Seconds())
		if status >= 500 {
			promErrors.Inc()
		}

		// Décider une fois si on sample cet événement (DogStatsD)
		sampled := shouldSample()
		if sampled {
			c.Increment("requests")
			c.Timing("request_duration_ms", latency)
		}
		if status >= 500 {
			c.Increment("errors")
		}

		// Log JSON via TCP (erreurs toujours, info selon sampling)
		ev := LogEvent{
			Service: service,
			Env:     env,
			Level:   levelFromStatus(status),
			Msg:     "handled request",
			Path:    r.URL.Path,
			Status:  status,
			Latency: latencyMs,
			Time:    time.Now().Format(time.RFC3339),
		}
		if status >= 500 || sampled {
			b, _ := json.Marshal(ev)
			fmt.Fprintln(conn, string(b))
		}
	})

	// Endpoint de contrôle pour ajuster le taux de sampling
	mux.HandleFunc("/control/sampling", func(w http.ResponseWriter, r *http.Request) {
		rateStr := r.URL.Query().Get("rate")
		if rateStr == "" {
			curr := sampleRate.Load()
			fmt.Fprintf(w, "current_rate=%v\n", curr)
			return
		}
		rate, err := strconv.ParseFloat(rateStr, 64)
		if err != nil {
			http.Error(w, "invalid rate", http.StatusBadRequest)
			return
		}
		if rate < 0 {
			rate = 0
		}
		if rate > 1 {
			rate = 1
		}
		sampleRate.Store(rate)
		fmt.Fprintf(w, "ok rate=%.3f\n", rate)
	})

	addr := ":8080"
	log.Printf("Go API listening on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatal(err)
	}
}

// getenv = lire variable d'env, ou valeur par défaut si non définie
func getenv(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}

// Retourne "error" si code >=500, sinon "info"

// shouldSample décide si on garde l'événement selon le taux courant
func shouldSample() bool {
	v := sampleRate.Load()
	if v == nil {
		return true
	}
	rate, ok := v.(float64)
	if !ok {
		return true
	}
	if rate >= 1 {
		return true
	}
	if rate <= 0 {
		return false
	}
	return rand.Float64() < rate
}

func levelFromStatus(code int) string {
	if code >= 500 {
		return "error"
	}
	return "info"
}
