"""
Volundr Scaffold Go microservice templates.

Go service templates extracted from _microservice_ts_go_templates.py.
"""

from typing import List, Tuple

from Asgard.Volundr.Scaffold.models.scaffold_models import (
    FileEntry,
    ServiceConfig,
)


def go_mod(config: ServiceConfig) -> str:
    return f'''module {config.name}

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
)
'''


def go_main(config: ServiceConfig) -> str:
    return f'''package main

import (
    "log"
    "{config.name}/internal/config"
    "{config.name}/internal/handlers"
    "github.com/gin-gonic/gin"
)

func main() {{
    cfg := config.Load()

    r := gin.Default()

    // Health routes
    r.GET("/health", handlers.HealthCheck)
    r.GET("/health/ready", handlers.ReadinessCheck)
    r.GET("/health/live", handlers.LivenessCheck)

    // Root route
    r.GET("/", func(c *gin.Context) {{
        c.JSON(200, gin.H{{"message": "Welcome to {config.name}"}})
    }})

    log.Printf("Starting server on port %d", cfg.Port)
    if err := r.Run(fmt.Sprintf(":%d", cfg.Port)); err != nil {{
        log.Fatal(err)
    }}
}}
'''


def go_config(config: ServiceConfig) -> str:
    return f'''package config

import (
    "os"
    "strconv"
)

type Config struct {{
    Port int
    Env  string
}}

func Load() *Config {{
    port := {config.port}
    if p := os.Getenv("PORT"); p != "" {{
        if parsed, err := strconv.Atoi(p); err == nil {{
            port = parsed
        }}
    }}

    return &Config{{
        Port: port,
        Env:  getEnv("ENV", "development"),
    }}
}}

func getEnv(key, defaultValue string) string {{
    if value := os.Getenv(key); value != "" {{
        return value
    }}
    return defaultValue
}}
'''


def go_health_handler(config: ServiceConfig) -> str:
    return '''package handlers

import (
    "github.com/gin-gonic/gin"
)

func HealthCheck(c *gin.Context) {
    c.JSON(200, gin.H{"status": "healthy"})
}

func ReadinessCheck(c *gin.Context) {
    c.JSON(200, gin.H{"status": "ready"})
}

func LivenessCheck(c *gin.Context) {
    c.JSON(200, gin.H{"status": "alive"})
}
'''


def go_dockerfile(config: ServiceConfig) -> str:
    return f'''FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o server ./cmd/server

FROM gcr.io/distroless/static-debian12

COPY --from=builder /app/server /server

EXPOSE {config.port}

USER nonroot:nonroot

ENTRYPOINT ["/server"]
'''


def generate_go_service(config: ServiceConfig) -> Tuple[List[FileEntry], List[str]]:
    files: List[FileEntry] = []
    directories: List[str] = [
        f"{config.name}",
        f"{config.name}/cmd",
        f"{config.name}/cmd/server",
        f"{config.name}/internal",
        f"{config.name}/internal/handlers",
        f"{config.name}/internal/services",
        f"{config.name}/internal/config",
        f"{config.name}/pkg",
    ]

    if config.include_tests:
        directories.append(f"{config.name}/internal/handlers")

    files.append(FileEntry(path=f"{config.name}/go.mod", content=go_mod(config)))
    files.append(FileEntry(
        path=f"{config.name}/cmd/server/main.go",
        content=go_main(config),
    ))
    files.append(FileEntry(
        path=f"{config.name}/internal/config/config.go",
        content=go_config(config),
    ))

    if config.include_healthcheck:
        files.append(FileEntry(
            path=f"{config.name}/internal/handlers/health.go",
            content=go_health_handler(config),
        ))

    if config.include_docker:
        files.append(FileEntry(
            path=f"{config.name}/Dockerfile",
            content=go_dockerfile(config),
        ))

    return files, directories
