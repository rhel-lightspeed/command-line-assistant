//! CLAD: Ollama-Compatible Chat Completions API
//!
//! This service provides an Ollama-compatible chat completions API that can be used
//! as a provider for other AI clients.
//!
//! CLAD always listens on 127.0.0.1:8080 for incoming requests.
//!
//! 1. Build and run the service:
//!    $ cargo run --release
//!
//! API COMPATIBILITY:
//! - Supports OpenAI-compatible chat completions API
//! - Compatible with Ollama's extended features (tool calling)
//! - Handles both streaming and non-streaming requests
//!
mod config;
mod openai;
mod provider;
mod state;

use axum::{
    routing::{get, post},
    Router,
};
use std::{net::SocketAddr, path::Path, sync::Arc};
use tracing::info;

use crate::{
    config::Config,
    provider::{
        chat_completions_handler, create_authenticated_client, health_check_handler, models_handler,
    },
    state::AppState,
};

/// Main entry point for the proxy server
#[tokio::main]
async fn main() {
    // Load configuration first (before logging is initialized)
    let config_path = std::env::var("XDG_CONFIG_DIRS").unwrap_or_else(|_| "/etc/xdg".to_string());
    let config_file = Path::new(&config_path)
        .join("command-line-assistant")
        .join("config.toml");

    // Load config to get the log level
    let config = match std::fs::read_to_string(&config_file) {
        Ok(contents) => {
            match toml::from_str::<Config>(&contents) {
                Ok(cfg) => cfg,
                Err(e) => {
                    eprintln!(
                        "Failed to parse config from {}: {}",
                        config_file.display(),
                        e
                    );
                    eprintln!("Please check your config.toml file. See config.toml.example for reference.");
                    std::process::exit(1);
                }
            }
        }
        Err(e) => {
            eprintln!(
                "Failed to read config from {}: {}",
                config_file.display(),
                e
            );
            eprintln!("Please create a config.toml file. See config.toml.example for reference.");
            std::process::exit(1);
        }
    };

    // Initialize logging with the configured log level
    let filter_string = config.get_tracing_filter();
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| filter_string.into()),
        )
        .init();

    // Now emit deprecation warnings if needed
    if config.database.is_some() {
        tracing::warn!("The [database] configuration section is deprecated and will be removed in a future version");
    }

    if config.history.is_some() {
        tracing::warn!("The [history] configuration section is deprecated and will be removed in a future version");
    }

    if config.logging.audit.is_some() {
        tracing::warn!("The [logging.audit] configuration section is deprecated and will be removed in a future version");
    }

    info!("Using log level from config: {}", config.logging.level);

    // CLAD always listens on 127.0.0.1:8080
    const LISTEN_HOST: &str = "127.0.0.1";
    const LISTEN_PORT: u16 = 8080;

    info!("Starting CLAD service on {}:{}", LISTEN_HOST, LISTEN_PORT);
    info!("Backend endpoint: {}", config.backend.endpoint);

    if let Some(proxies) = &config.backend.proxies {
        if !proxies.is_empty() {
            info!("HTTP/HTTPS proxy will be used for outgoing backend requests");
            if let Some(http) = proxies.get("http") {
                info!("  HTTP proxy: {}", http);
            }
            if let Some(https) = proxies.get("https") {
                info!("  HTTPS proxy: {}", https);
            }
        }
    }

    // Create HTTP client with certificate-based authentication
    let client = create_authenticated_client(&config).unwrap_or_else(|e| {
        eprintln!("Failed to create HTTP client: {}", e);
        std::process::exit(1);
    });

    // Create shared state
    let config_arc = Arc::new(config);
    let state = AppState {
        config: config_arc.clone(),
        client,
    };

    // Build application with all middleware
    let app = Router::new()
        .route("/health", get(health_check_handler))
        .route("/v1/chat/completions", post(chat_completions_handler))
        .route("/v1/models", get(models_handler))
        .with_state(state);

    // Bind and serve
    let addr = format!("{}:{}", LISTEN_HOST, LISTEN_PORT);
    let socket_addr: SocketAddr = addr.parse().unwrap_or_else(|e| {
        eprintln!("Invalid address '{}': {}", addr, e);
        std::process::exit(1);
    });

    let listener = tokio::net::TcpListener::bind(socket_addr)
        .await
        .unwrap_or_else(|e| {
            eprintln!("Failed to bind to {}: {}", socket_addr, e);
            eprintln!("Make sure the port is not in use and you have proper permissions");
            std::process::exit(1);
        });

    info!("CLAD service listening on {}", socket_addr);

    if let Err(e) = axum::serve(listener, app).await {
        eprintln!("Server error: {}", e);
        std::process::exit(1);
    }
}
