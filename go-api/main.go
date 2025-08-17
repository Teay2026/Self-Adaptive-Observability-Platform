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
	"time"          // pour mesurer le temps d'exécution et ajouter des horodatages

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

func main() {
	// ============================
	// 1) Lire la config via les variables d'environnement
	// ============================
	statsdAddr := getenv("STATSD_ADDR", "vector:8125") // UDP DogStatsD vers Vector
	logAddr := getenv("LOG_TARGET", "vector:9000")     // TCP logs vers Vector
	service := getenv("SERVICE_NAME", "api")
	env := getenv("ENV", "dev")

	// ============================
	// 2) Connexion UDP au client DogStatsD
	// ============================
	c, err := statsd.New(
		statsd.Address(statsdAddr),        // où envoyer
		statsd.Prefix("api."),             // préfixe pour toutes les métriques
		statsd.TagsFormat(statsd.Datadog), // format de tags DogStatsD
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

		// Latence en ms pour le log
		latencyMs := float64(time.Since(start).Milliseconds())

		// 4a) Émettre métriques DogStatsD
		c.Increment("requests")                            // api_requests_total
		c.Timing("request_duration_ms", time.Since(start)) // api_request_duration_ms_{sum,count}

		// 👉 NOUVEAU : incrémente le compteur d’erreurs si status >= 500
		if status >= 500 {
			c.Increment("errors") // api_errors_total
		}

		// 4b) Écrire un log JSON via TCP
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
		b, _ := json.Marshal(ev)
		fmt.Fprintln(conn, string(b))
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
func levelFromStatus(code int) string {
	if code >= 500 {
		return "error"
	}
	return "info"
}