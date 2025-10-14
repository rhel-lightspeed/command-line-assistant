// Library interface for clad-redux
// This allows integration tests and external crates to use our modules

use std::sync::Arc;

use crate::config;

/// Application state shared across handlers
#[derive(Clone, Debug)]
pub struct AppState {
    /// Configuration
    pub config: Arc<config::Config>,
    /// HTTP client for backend requests
    pub client: reqwest::Client,
}
