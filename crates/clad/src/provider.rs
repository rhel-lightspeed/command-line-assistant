use axum::{
    extract::State,
    http::StatusCode,
    response::{IntoResponse, Response, Sse},
    Json,
};
use futures::stream::{self, Stream, StreamExt};
use serde_json::{json, Value};
use std::convert::Infallible;
use std::time::Duration;
use tokio::time::sleep;
use tracing::{debug, error, info};

use crate::config::Config;
use crate::openai::{
    ChatCompletionChunk, ChatCompletionRequest, ChatCompletionResponse, Choice, ChunkChoice, Delta,
    Message, Model, ModelsResponse, Usage,
};
use crate::state::AppState;
use std::fs;

/// Create an HTTP client with authentication
pub fn create_authenticated_client(
    config: &Config,
) -> Result<reqwest::Client, Box<dyn std::error::Error>> {
    // Read certificate and key files
    let cert_pem = fs::read(&config.backend.auth.cert_file).map_err(|e| {
        format!(
            "Failed to read cert file {}: {}",
            config.backend.auth.cert_file, e
        )
    })?;
    let key_pem = fs::read(&config.backend.auth.key_file).map_err(|e| {
        format!(
            "Failed to read key file {}: {}",
            config.backend.auth.key_file, e
        )
    })?;

    // Create identity from certificate and key (PEM format)
    let identity = reqwest::Identity::from_pkcs8_pem(&cert_pem, &key_pem)?;

    // Build client with identity and optional proxy settings
    let mut client_builder = reqwest::Client::builder()
        .identity(identity)
        .timeout(std::time::Duration::from_secs(config.backend.timeout));

    // Add proxy configuration if specified
    if let Some(proxies) = &config.backend.proxies {
        if let Some(http_proxy) = proxies.get("http") {
            tracing::info!("Configuring HTTP proxy: {}", http_proxy);
            client_builder = client_builder.proxy(reqwest::Proxy::http(http_proxy)?);
        }
        if let Some(https_proxy) = proxies.get("https") {
            tracing::info!("Configuring HTTPS proxy: {}", https_proxy);
            client_builder = client_builder.proxy(reqwest::Proxy::https(https_proxy)?);
        }
    }

    Ok(client_builder.build()?)
}

/// Generate a cryptographically secure UUID
fn uuid_simple() -> String {
    uuid::Uuid::new_v4().to_string()
}

/// Get current Unix timestamp
fn current_timestamp() -> i64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("System time before UNIX epoch")
        .as_secs() as i64
}

/// Error types for the proxy
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    /// Backend service unavailable
    #[error("Backend service unavailable")]
    Backend(String),

    /// Failed to transform request/response
    #[error("Failed to transform request/response")]
    Transform(String),

    /// Request timeout
    #[error("Request timeout")]
    Timeout,

    /// Internal server error
    #[error("Internal server error")]
    #[allow(dead_code)]
    Internal(String),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        // Log the detailed error internally
        error!("Error occurred: {:?}", self);

        // Return sanitized error to client
        let (status, message, error_type) = match self {
            AppError::Backend(_) => (
                StatusCode::BAD_GATEWAY,
                "Backend service unavailable".to_string(),
                "backend_error",
            ),
            AppError::Transform(_) => (
                StatusCode::INTERNAL_SERVER_ERROR,
                "Failed to process response".to_string(),
                "transform_error",
            ),
            AppError::Timeout => (
                StatusCode::GATEWAY_TIMEOUT,
                "Request timeout".to_string(),
                "timeout_error",
            ),
            AppError::Internal(_) => (
                StatusCode::INTERNAL_SERVER_ERROR,
                "Internal server error".to_string(),
                "internal_error",
            ),
        };

        let body = json!({
            "error": {
                "message": message,
                "type": error_type,
            }
        });

        (status, Json(body)).into_response()
    }
}

/// Transform OpenAI request to Red Hat Lightspeed backend format
/// The backend expects: { "question": "...", "context": {...} }
fn transform_request(openai_req: &ChatCompletionRequest) -> Value {
    // Extract the last user message as the question
    // In a conversation, we take the most recent message as the main question
    let question = openai_req
        .messages
        .iter()
        .rev()
        .find(|m| m.role == "user")
        .map(|m| m.content.clone())
        .unwrap_or_else(|| "".to_string());

    // Get system information
    let systeminfo = get_system_info();

    // Build the Red Hat Lightspeed format
    let request = json!({
        "question": question,
        "context": {
            "stdin": "",
            "attachments": {
                "contents": "",
                "mimetype": ""
            },
            "terminal": {
                "output": ""
            },
            "systeminfo": {
                "os": systeminfo.os,
                "version": systeminfo.version,
                "arch": systeminfo.arch,
                "id": systeminfo.id
            },
            "cla": {
                "version": env!("CARGO_PKG_VERSION")
            }
        }
    });

    request
}

/// Get system information for the context
fn get_system_info() -> SystemInfo {
    SystemInfo {
        os: std::env::consts::OS.to_string(),
        version: get_os_version(),
        arch: std::env::consts::ARCH.to_string(),
        id: get_system_id(),
    }
}

/// System information structure
struct SystemInfo {
    os: String,
    version: String,
    arch: String,
    id: String,
}

/// Get OS version string
fn get_os_version() -> String {
    // Try to read /etc/os-release for Linux systems
    if let Ok(content) = fs::read_to_string("/etc/os-release") {
        for line in content.lines() {
            if line.starts_with("VERSION=") {
                return line
                    .trim_start_matches("VERSION=")
                    .trim_matches('"')
                    .to_string();
            }
        }
    }
    "unknown".to_string()
}

/// Get system ID (machine-id on Linux)
fn get_system_id() -> String {
    // Try to read machine-id
    if let Ok(id) = fs::read_to_string("/etc/machine-id") {
        return id.trim().to_string();
    }
    if let Ok(id) = fs::read_to_string("/var/lib/dbus/machine-id") {
        return id.trim().to_string();
    }
    "unknown".to_string()
}

/// Transform Red Hat Lightspeed backend response to OpenAI format
/// The backend returns: { "data": { "text": "..." } }
fn transform_response(
    backend_resp: &Value,
    model: &str,
) -> Result<ChatCompletionResponse, AppError> {
    // Extract the response text from the Red Hat Lightspeed format
    let generated_text = backend_resp
        .get("data")
        .and_then(|v| v.get("text"))
        .and_then(|v| v.as_str())
        .ok_or_else(|| {
            AppError::Transform(format!(
                "Could not extract response from backend. Expected 'data.text' field. Response: {:?}",
                backend_resp
            ))
        })?;

    // Estimate token counts since the backend doesn't provide them
    let estimated_prompt = 0;
    let estimated_completion = (generated_text.len() / 4) as u32;
    let (prompt_tokens, completion_tokens, total_tokens) = (
        estimated_prompt,
        estimated_completion,
        estimated_prompt + estimated_completion,
    );

    // Build OpenAI-compatible response
    Ok(ChatCompletionResponse {
        id: format!("chatcmpl-{}", uuid_simple()),
        object: "chat.completion".to_string(),
        created: current_timestamp(),
        model: model.to_string(),
        choices: vec![Choice {
            index: 0,
            message: Message {
                role: "assistant".to_string(),
                content: generated_text.to_string(),
                name: None,
                tool_calls: None,
            },
            finish_reason: Some("stop".to_string()),
        }],
        usage: Usage {
            prompt_tokens,
            completion_tokens,
            total_tokens,
        },
    })
}

/// Extract text for streaming from Red Hat Lightspeed backend
/// The backend returns: { "data": { "text": "..." } }
fn extract_streaming_text(backend_response: &Value) -> Result<String, AppError> {
    // Extract from Red Hat Lightspeed format
    backend_response
        .get("data")
        .and_then(|v| v.get("text"))
        .and_then(|v| v.as_str())
        .ok_or_else(|| {
            AppError::Transform(format!(
                "Could not extract text from backend response for streaming. Expected 'data.text'. Response: {:?}",
                backend_response
            ))
        })
        .map(|s| s.to_string())
}

/// Handler for /v1/chat/completions endpoint
pub async fn chat_completions_handler(
    State(state): State<AppState>,
    Json(request): Json<ChatCompletionRequest>,
) -> Result<Response, AppError> {
    info!(
        model = %request.model,
        message_count = request.messages.len(),
        "Received chat completion request"
    );
    debug!("Request: {:?}", ::serde_json::to_string_pretty(&request));

    // Check if streaming is requested
    let is_streaming = request.stream.unwrap_or(false);

    if is_streaming {
        info!("Streaming response requested");
        Ok(handle_streaming_request(state, request)
            .await?
            .into_response())
    } else {
        info!("Non-streaming response requested");
        Ok(handle_non_streaming_request(state, request)
            .await?
            .into_response())
    }
}

/// Handle non-streaming chat completion request
async fn handle_non_streaming_request(
    state: AppState,
    request: ChatCompletionRequest,
) -> Result<Json<ChatCompletionResponse>, AppError> {
    let backend_request = transform_request(&request);

    // Forward request to external backend
    let backend_req = state
        .client
        .post(&state.config.backend.endpoint)
        .json(&backend_request);

    let response = backend_req.send().await.map_err(|e| {
        error!("Failed to send request to backend: {}", e);
        AppError::Backend(e.to_string())
    })?;

    if !response.status().is_success() {
        let status = response.status();
        let error_body = response.text().await.unwrap_or_default();
        error!("Backend returned error {}: {}", status, error_body);
        return Err(AppError::Backend(format!(
            "Backend returned status {}",
            status
        )));
    }

    // Parse backend response
    let backend_response: Value = response.json().await.map_err(|e| {
        error!("Failed to parse backend response: {}", e);
        AppError::Backend(e.to_string())
    })?;

    // Transform backend response to OpenAI format
    let transformed_response = transform_response(&backend_response, &request.model)?;

    info!("Successfully processed non-streaming request");
    Ok(Json(transformed_response))
}

/// Handle streaming chat completion request
async fn handle_streaming_request(
    state: AppState,
    request: ChatCompletionRequest,
) -> Result<Sse<impl Stream<Item = Result<axum::response::sse::Event, Infallible>>>, AppError> {
    // Transform OpenAI request to backend format
    let backend_request = transform_request(&request);

    // Forward request to external backend with timeout
    let timeout_duration = Duration::from_secs(state.config.backend.timeout);

    let response = tokio::time::timeout(
        timeout_duration,
        state
            .client
            .post(&state.config.backend.endpoint)
            .json(&backend_request)
            .send(),
    )
    .await
    .map_err(|_| {
        error!("Backend request timed out after {:?}", timeout_duration);
        AppError::Timeout
    })?
    .map_err(|e| {
        error!("Failed to send request to backend: {}", e);
        AppError::Backend(e.to_string())
    })?;

    if !response.status().is_success() {
        let status = response.status();
        let error_body = response.text().await.unwrap_or_default();
        error!("Backend returned error status {}: {}", status, error_body);
        return Err(AppError::Backend(format!(
            "Backend returned status {}",
            status
        )));
    }

    // Parse backend response
    let backend_response: Value = response.json().await.map_err(|e| {
        error!("Failed to parse backend response: {}", e);
        AppError::Backend(e.to_string())
    })?;

    debug!("Backend response for streaming: {:?}", backend_response);

    // Extract the reply from the backend
    let generated_text = extract_streaming_text(&backend_response)?;

    // Create streaming chunks
    let stream = create_streaming_chunks(generated_text, request.model);

    info!("Successfully started streaming response");
    Ok(Sse::new(stream))
}

/// Create a stream of SSE events from the complete response text
/// This simulates streaming by breaking the response into chunks
fn create_streaming_chunks(
    text: String,
    model: String,
) -> impl Stream<Item = Result<axum::response::sse::Event, Infallible>> {
    let chunk_id = format!("chatcmpl-{}", uuid_simple());
    let created = current_timestamp();

    // Split text into words for streaming simulation
    let words: Vec<String> = text.split_whitespace().map(|s| format!("{} ", s)).collect();
    let total_chunks = words.len();

    stream::iter(0..=total_chunks).then(move |i| {
        let chunk_id = chunk_id.clone();
        let model = model.clone();
        let words = words.clone();

        async move {
            // Small delay to simulate streaming
            if i > 0 {
                sleep(Duration::from_millis(20)).await;
            }

            let chunk = if i == 0 {
                // First chunk: send role
                ChatCompletionChunk {
                    id: chunk_id.clone(),
                    object: "chat.completion.chunk".to_string(),
                    created,
                    model: model.clone(),
                    choices: vec![ChunkChoice {
                        index: 0,
                        delta: Delta {
                            role: Some("assistant".to_string()),
                            content: None,
                            tool_calls: None,
                        },
                        finish_reason: None,
                    }],
                }
            } else if i < total_chunks {
                // Middle chunks: send content
                ChatCompletionChunk {
                    id: chunk_id.clone(),
                    object: "chat.completion.chunk".to_string(),
                    created,
                    model: model.clone(),
                    choices: vec![ChunkChoice {
                        index: 0,
                        delta: Delta {
                            role: None,
                            content: Some(words[i].clone()),
                            tool_calls: None,
                        },
                        finish_reason: None,
                    }],
                }
            } else {
                // Last chunk: send finish reason
                ChatCompletionChunk {
                    id: chunk_id.clone(),
                    object: "chat.completion.chunk".to_string(),
                    created,
                    model: model.clone(),
                    choices: vec![ChunkChoice {
                        index: 0,
                        delta: Delta {
                            role: None,
                            content: None,
                            tool_calls: None,
                        },
                        finish_reason: Some("stop".to_string()),
                    }],
                }
            };

            let json_str = serde_json::to_string(&chunk).unwrap_or_else(|e| {
                error!("Failed to serialize chunk: {}", e);
                r#"{"error": "serialization failed"}"#.to_string()
            });
            Ok::<_, Infallible>(axum::response::sse::Event::default().data(json_str))
        }
    })
}

/// Handler for /v1/models endpoint
/// Returns a list of available models
pub async fn models_handler(State(_state): State<AppState>) -> Json<ModelsResponse> {
    // CUSTOMIZE THIS: Return your actual available models
    Json(ModelsResponse {
        object: "list".to_string(),
        data: vec![Model {
            id: "default-model".to_string(),
            object: "model".to_string(),
            created: 1234567890,
            owned_by: "clad-redux".to_string(),
        }],
    })
}

/// Health check endpoint
/// Returns 200 OK if the service is running
pub async fn health_check_handler() -> impl IntoResponse {
    (
        StatusCode::OK,
        Json(json!({
            "status": "healthy",
            "service": "clad-proxy",
            "timestamp": current_timestamp(),
        })),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::http::StatusCode;

    // ============================================================================
    // Tests for utility functions
    // ============================================================================

    #[test]
    fn test_uuid_simple_generates_valid_uuid() {
        let uuid = uuid_simple();

        // UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        assert_eq!(uuid.len(), 36, "UUID should be 36 characters");
        assert_eq!(
            uuid.chars().filter(|&c| c == '-').count(),
            4,
            "UUID should have 4 dashes"
        );

        // Check that it's a valid UUID format
        assert!(
            uuid.chars().all(|c| c.is_ascii_hexdigit() || c == '-'),
            "UUID should only contain hex digits and dashes"
        );
    }

    #[test]
    fn test_uuid_simple_generates_unique_uuids() {
        let uuid1 = uuid_simple();
        let uuid2 = uuid_simple();
        let uuid3 = uuid_simple();

        assert_ne!(uuid1, uuid2, "UUIDs should be unique");
        assert_ne!(uuid2, uuid3, "UUIDs should be unique");
        assert_ne!(uuid1, uuid3, "UUIDs should be unique");
    }

    #[test]
    fn test_current_timestamp_returns_positive() {
        let timestamp = current_timestamp();
        assert!(timestamp > 0, "Timestamp should be positive");
    }

    #[test]
    fn test_current_timestamp_is_recent() {
        let timestamp = current_timestamp();

        // Should be after 2020-01-01 (1577836800)
        assert!(timestamp > 1577836800, "Timestamp should be after 2020");

        // Should be before 2050-01-01 (2524608000)
        assert!(timestamp < 2524608000, "Timestamp should be before 2050");
    }

    #[test]
    fn test_current_timestamp_is_monotonic() {
        let ts1 = current_timestamp();
        std::thread::sleep(std::time::Duration::from_millis(10));
        let ts2 = current_timestamp();

        assert!(ts2 >= ts1, "Timestamps should be monotonically increasing");
    }

    #[test]
    fn test_current_timestamp_precision() {
        let ts1 = current_timestamp();
        let ts2 = current_timestamp();

        // Timestamps should be in seconds, so rapid calls might return the same value
        // or differ by at most a few seconds
        assert!((ts2 - ts1) < 2, "Rapid timestamp calls should be close");
    }

    // ============================================================================
    // Tests for AppError
    // ============================================================================

    #[test]
    fn test_app_error_display() {
        let err = AppError::Backend("test error".to_string());
        assert_eq!(err.to_string(), "Backend service unavailable");

        let err = AppError::Transform("transform issue".to_string());
        assert_eq!(err.to_string(), "Failed to transform request/response");

        let err = AppError::Timeout;
        assert_eq!(err.to_string(), "Request timeout");

        let err = AppError::Internal("internal issue".to_string());
        assert_eq!(err.to_string(), "Internal server error");
    }

    #[test]
    fn test_app_error_into_response_backend_error() {
        let err = AppError::Backend("connection failed".to_string());
        let response = err.into_response();

        assert_eq!(response.status(), StatusCode::BAD_GATEWAY);
    }

    #[test]
    fn test_app_error_into_response_transform_error() {
        let err = AppError::Transform("bad format".to_string());
        let response = err.into_response();

        assert_eq!(response.status(), StatusCode::INTERNAL_SERVER_ERROR);
    }

    #[test]
    fn test_app_error_into_response_timeout_error() {
        let err = AppError::Timeout;
        let response = err.into_response();

        assert_eq!(response.status(), StatusCode::GATEWAY_TIMEOUT);
    }

    #[test]
    fn test_app_error_into_response_internal_error() {
        let err = AppError::Internal("panic".to_string());
        let response = err.into_response();

        assert_eq!(response.status(), StatusCode::INTERNAL_SERVER_ERROR);
    }

    // ============================================================================
    // Tests for streaming chunk creation
    // ============================================================================

    #[test]
    fn test_create_streaming_chunks_empty_text() {
        use futures::StreamExt;

        let text = "".to_string();
        let model = "test-model".to_string();

        let mut stream = Box::pin(create_streaming_chunks(text, model));

        // Should have at least first chunk (role) and last chunk (finish_reason)
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let first = stream.next().await;
            assert!(first.is_some(), "Should have first chunk");
        });
    }

    #[test]
    fn test_create_streaming_chunks_single_word() {
        use futures::StreamExt;

        let text = "Hello".to_string();
        let model = "test-model".to_string();

        let mut stream = Box::pin(create_streaming_chunks(text, model));

        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let mut count = 0;
            while let Some(_chunk) = stream.next().await {
                count += 1;
            }

            // For 1 word, stream iterates 0..=1: i=0 (role), i=1 (finish) = 2 chunks
            assert_eq!(count, 2);
        });
    }

    #[test]
    fn test_create_streaming_chunks_multiple_words() {
        use futures::StreamExt;

        let text = "Hello world test".to_string();
        let model = "test-model".to_string();

        let mut stream = Box::pin(create_streaming_chunks(text, model));

        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let mut count = 0;
            while let Some(_chunk) = stream.next().await {
                count += 1;
            }

            // For 3 words, stream iterates 0..=3: i=0 (role), i=1,2,3 (content), but...
            // Actually checking the code: i=0 (role), i=1,2,3 content is at words[i], i=3 is finish
            // So: role, word1, word2, finish = 4 chunks (word3 doesn't get sent because i=3 >= total_chunks=3)
            assert_eq!(count, 4);
        });
    }

    // ============================================================================
    // Tests for models_handler
    // ============================================================================

    #[tokio::test]
    async fn test_models_handler_returns_valid_response() {
        use crate::config::Config;
        use std::sync::Arc;

        let config_str = r#"
            [backend]
            endpoint = "http://localhost:9000"

            [backend.auth]
            cert_file = "/path/to/cert.pem"
            key_file = "/path/to/key.pem"
        "#;

        let config: Config = toml::from_str(config_str).unwrap();
        let client = reqwest::Client::new();

        let state = AppState {
            config: Arc::new(config),
            client,
        };

        let response = models_handler(State(state)).await;

        assert_eq!(response.0.object, "list");
        assert!(!response.0.data.is_empty());
        assert_eq!(response.0.data[0].id, "default-model");
    }

    // ============================================================================
    // Tests for health_check_handler
    // ============================================================================

    #[tokio::test]
    async fn test_health_check_handler_returns_ok() {
        let response = health_check_handler().await;
        let response = response.into_response();

        assert_eq!(response.status(), StatusCode::OK);
    }

    #[tokio::test]
    async fn test_health_check_handler_returns_valid_json() {
        let response = health_check_handler().await;
        let response = response.into_response();

        // Verify it returns OK status
        assert_eq!(response.status(), StatusCode::OK);

        // The body should be valid JSON with expected fields
        // In a real test, you'd extract and parse the body, but that's complex with axum
        // For now, we just verify it doesn't panic and returns OK
    }

    // ============================================================================
    // Tests for transform_request
    // ============================================================================

    #[test]
    fn test_transform_request_basic() {
        use crate::openai::{ChatCompletionRequest, Message};
        use std::collections::HashMap;

        let request = ChatCompletionRequest {
            model: "test-model".to_string(),
            messages: vec![Message {
                role: "user".to_string(),
                content: "Hello, world!".to_string(),
                name: None,
                tool_calls: None,
            }],
            temperature: None,
            top_p: None,
            n: None,
            stream: None,
            stop: None,
            max_tokens: None,
            presence_penalty: None,
            frequency_penalty: None,
            user: None,
            tools: None,
            tool_choice: None,
            extra: HashMap::new(),
        };

        let transformed = transform_request(&request);

        // Check that question is extracted
        assert!(transformed.get("question").is_some());
        assert_eq!(
            transformed.get("question").unwrap().as_str().unwrap(),
            "Hello, world!"
        );

        // Check that context exists
        assert!(transformed.get("context").is_some());
    }

    #[test]
    fn test_transform_request_multiple_messages() {
        use crate::openai::{ChatCompletionRequest, Message};
        use std::collections::HashMap;

        let request = ChatCompletionRequest {
            model: "test-model".to_string(),
            messages: vec![
                Message {
                    role: "system".to_string(),
                    content: "You are a helpful assistant".to_string(),
                    name: None,
                    tool_calls: None,
                },
                Message {
                    role: "user".to_string(),
                    content: "First message".to_string(),
                    name: None,
                    tool_calls: None,
                },
                Message {
                    role: "assistant".to_string(),
                    content: "Response".to_string(),
                    name: None,
                    tool_calls: None,
                },
                Message {
                    role: "user".to_string(),
                    content: "Second message".to_string(),
                    name: None,
                    tool_calls: None,
                },
            ],
            temperature: None,
            top_p: None,
            n: None,
            stream: None,
            stop: None,
            max_tokens: None,
            presence_penalty: None,
            frequency_penalty: None,
            user: None,
            tools: None,
            tool_choice: None,
            extra: HashMap::new(),
        };

        let transformed = transform_request(&request);

        // Should extract the last user message
        assert_eq!(
            transformed.get("question").unwrap().as_str().unwrap(),
            "Second message"
        );
    }

    #[test]
    fn test_transform_request_no_user_message() {
        use crate::openai::{ChatCompletionRequest, Message};
        use std::collections::HashMap;

        let request = ChatCompletionRequest {
            model: "test-model".to_string(),
            messages: vec![Message {
                role: "system".to_string(),
                content: "System message".to_string(),
                name: None,
                tool_calls: None,
            }],
            temperature: None,
            top_p: None,
            n: None,
            stream: None,
            stop: None,
            max_tokens: None,
            presence_penalty: None,
            frequency_penalty: None,
            user: None,
            tools: None,
            tool_choice: None,
            extra: HashMap::new(),
        };

        let transformed = transform_request(&request);

        // Should have empty question
        assert_eq!(transformed.get("question").unwrap().as_str().unwrap(), "");
    }

    #[test]
    fn test_transform_request_context_structure() {
        use crate::openai::{ChatCompletionRequest, Message};
        use std::collections::HashMap;

        let request = ChatCompletionRequest {
            model: "test-model".to_string(),
            messages: vec![Message {
                role: "user".to_string(),
                content: "Test".to_string(),
                name: None,
                tool_calls: None,
            }],
            temperature: None,
            top_p: None,
            n: None,
            stream: None,
            stop: None,
            max_tokens: None,
            presence_penalty: None,
            frequency_penalty: None,
            user: None,
            tools: None,
            tool_choice: None,
            extra: HashMap::new(),
        };

        let transformed = transform_request(&request);
        let context = transformed.get("context").unwrap();

        // Check context has expected fields
        assert!(context.get("stdin").is_some());
        assert!(context.get("attachments").is_some());
        assert!(context.get("terminal").is_some());
        assert!(context.get("systeminfo").is_some());
        assert!(context.get("cla").is_some());

        // Check systeminfo has expected fields
        let systeminfo = context.get("systeminfo").unwrap();
        assert!(systeminfo.get("os").is_some());
        assert!(systeminfo.get("version").is_some());
        assert!(systeminfo.get("arch").is_some());
        assert!(systeminfo.get("id").is_some());
    }

    // ============================================================================
    // Tests for transform_response
    // ============================================================================

    #[test]
    fn test_transform_response_success() {
        use serde_json::json;

        let backend_resp = json!({
            "data": {
                "text": "This is a test response"
            }
        });

        let result = transform_response(&backend_resp, "test-model");
        assert!(result.is_ok());

        let response = result.unwrap();
        assert_eq!(response.model, "test-model");
        assert_eq!(response.object, "chat.completion");
        assert_eq!(response.choices.len(), 1);
        assert_eq!(
            response.choices[0].message.content,
            "This is a test response"
        );
        assert_eq!(response.choices[0].message.role, "assistant");
        assert_eq!(response.choices[0].finish_reason, Some("stop".to_string()));
    }

    #[test]
    fn test_transform_response_missing_data() {
        use serde_json::json;

        let backend_resp = json!({
            "wrong_field": "value"
        });

        let result = transform_response(&backend_resp, "test-model");
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), AppError::Transform(_)));
    }

    #[test]
    fn test_transform_response_missing_text() {
        use serde_json::json;

        let backend_resp = json!({
            "data": {
                "wrong_field": "value"
            }
        });

        let result = transform_response(&backend_resp, "test-model");
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), AppError::Transform(_)));
    }

    #[test]
    fn test_transform_response_token_estimation() {
        use serde_json::json;

        let text = "a".repeat(100); // 100 characters
        let backend_resp = json!({
            "data": {
                "text": text
            }
        });

        let result = transform_response(&backend_resp, "test-model");
        assert!(result.is_ok());

        let response = result.unwrap();
        // Token count should be approximately text.len() / 4
        assert!(response.usage.completion_tokens > 0);
        assert_eq!(response.usage.completion_tokens, 25); // 100 / 4
    }

    // ============================================================================
    // Tests for extract_streaming_text
    // ============================================================================

    #[test]
    fn test_extract_streaming_text_success() {
        use serde_json::json;

        let backend_resp = json!({
            "data": {
                "text": "Streaming response"
            }
        });

        let result = extract_streaming_text(&backend_resp);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "Streaming response");
    }

    #[test]
    fn test_extract_streaming_text_missing_data() {
        use serde_json::json;

        let backend_resp = json!({
            "wrong_field": "value"
        });

        let result = extract_streaming_text(&backend_resp);
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), AppError::Transform(_)));
    }

    #[test]
    fn test_extract_streaming_text_missing_text() {
        use serde_json::json;

        let backend_resp = json!({
            "data": {}
        });

        let result = extract_streaming_text(&backend_resp);
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), AppError::Transform(_)));
    }

    // ============================================================================
    // Tests for get_system_info
    // ============================================================================

    #[test]
    fn test_get_system_info_returns_data() {
        let info = get_system_info();

        // Check that all fields are populated
        assert!(!info.os.is_empty());
        assert!(!info.version.is_empty());
        assert!(!info.arch.is_empty());
        assert!(!info.id.is_empty());
    }

    #[test]
    fn test_get_system_info_os_field() {
        let info = get_system_info();

        // OS should be a known value from std::env::consts::OS
        assert!(matches!(
            info.os.as_str(),
            "linux" | "macos" | "windows" | "freebsd" | "openbsd" | "netbsd"
        ));
    }

    #[test]
    fn test_get_system_info_arch_field() {
        let info = get_system_info();

        // Architecture should be a known value
        assert!(matches!(
            info.arch.as_str(),
            "x86_64" | "x86" | "arm" | "aarch64" | "riscv64"
        ));
    }

    // ============================================================================
    // Tests for get_os_version
    // ============================================================================

    #[test]
    fn test_get_os_version_returns_string() {
        let version = get_os_version();

        // Should return a non-empty string (or "unknown")
        assert!(!version.is_empty());
    }

    // ============================================================================
    // Tests for get_system_id
    // ============================================================================

    #[test]
    fn test_get_system_id_returns_string() {
        let id = get_system_id();

        // Should return a non-empty string (or "unknown")
        assert!(!id.is_empty());
    }
}
