package main

import (
	"log"
	"os"

	"github.com/company/go-product-service/internal/api"
	"github.com/company/go-product-service/internal/config"
	"github.com/company/go-product-service/internal/database"
	"github.com/company/go-product-service/internal/repository"
	"github.com/company/go-product-service/internal/service"
	"github.com/company/go-product-service/pkg/logger"
	"github.com/joho/godotenv"
)

// @title Product Service API
// @version 1.0
// @description A microservice for managing products
// @termsOfService http://swagger.io/terms/

// @contact.name API Support
// @contact.url http://www.swagger.io/support
// @contact.email support@swagger.io

// @license.name MIT
// @license.url https://opensource.org/licenses/MIT

// @host localhost:8080
// @BasePath /api/v1

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using system environment variables")
	}

	// Initialize logger
	logger := logger.NewLogger()
	defer logger.Sync()

	// Load configuration
	cfg := config.Load()

	// Initialize database
	db, err := database.NewPostgresDB(cfg.DatabaseURL)
	if err != nil {
		logger.Fatal("Failed to connect to database", err)
	}
	defer db.Close()

	// Run migrations
	if err := database.RunMigrations(cfg.DatabaseURL); err != nil {
		logger.Fatal("Failed to run migrations", err)
	}

	// Initialize repositories
	productRepo := repository.NewProductRepository(db)

	// Initialize services
	productService := service.NewProductService(productRepo, logger)

	// Initialize API server
	server := api.NewServer(productService, logger)

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	logger.Info("Starting server on port " + port)
	if err := server.Start(":" + port); err != nil {
		logger.Fatal("Server failed to start", err)
	}
}
