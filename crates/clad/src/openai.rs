use serde::{Deserialize, Serialize};
use serde_json::Value;

/// OpenAI chat completion request structure
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChatCompletionRequest {
    /// Model ID
    pub model: String,
    /// List of messages
    pub messages: Vec<Message>,
    /// Temperature
    #[serde(default)]
    pub temperature: Option<f32>,
    /// Top P
    #[serde(default)]
    pub top_p: Option<f32>,
    /// Number of completions
    #[serde(default)]
    pub n: Option<u32>,
    /// Stream
    #[serde(default)]
    pub stream: Option<bool>,
    /// Stop
    #[serde(default)]
    pub stop: Option<Vec<String>>,
    /// Maximum tokens
    #[serde(default)]
    pub max_tokens: Option<u32>,
    /// Presence penalty
    #[serde(default)]
    pub presence_penalty: Option<f32>,
    /// Frequency penalty
    #[serde(default)]
    pub frequency_penalty: Option<f32>,
    /// User
    #[serde(default)]
    pub user: Option<String>,
    /// Tools
    #[serde(default)]
    pub tools: Option<Vec<Tool>>,
    /// Tool choice
    #[serde(default)]
    pub tool_choice: Option<Value>,
    /// Additional fields that might be present
    #[serde(flatten)]
    pub extra: std::collections::HashMap<String, Value>,
}

/// Chat message structure
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Message {
    /// Role
    pub role: String,
    /// Content
    #[serde(default)]
    pub content: String,
    /// Name
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    /// Tool calls
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_calls: Option<Vec<ToolCall>>,
}

/// Tool call structure for function calling
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ToolCall {
    /// ID
    pub id: String,
    /// Call type
    #[serde(rename = "type")]
    pub call_type: String,
    /// Function
    pub function: FunctionCall,
}

/// Function call details
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct FunctionCall {
    /// Name
    pub name: String,
    /// Arguments
    pub arguments: String,
}

/// Tool definition structure
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Tool {
    /// Tool type
    #[serde(rename = "type")]
    pub tool_type: String,
    /// Function
    pub function: FunctionDefinition,
}

/// Function definition for tools
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct FunctionDefinition {
    /// Name
    pub name: String,
    /// Description
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    /// Parameters
    pub parameters: Value,
}

/// OpenAI chat completion response structure
#[derive(Debug, Serialize, Deserialize)]
pub struct ChatCompletionResponse {
    /// ID
    pub id: String,
    /// Object
    pub object: String,
    /// Created
    pub created: i64,
    /// Model
    pub model: String,
    /// Choices
    pub choices: Vec<Choice>,
    /// Usage
    pub usage: Usage,
}

/// Choice structure
#[derive(Debug, Serialize, Deserialize)]
pub struct Choice {
    /// Index
    pub index: u32,
    /// Message
    pub message: Message,
    /// Finish reason
    pub finish_reason: Option<String>,
}

/// Usage structure
#[derive(Debug, Serialize, Deserialize)]
pub struct Usage {
    /// Prompt tokens
    pub prompt_tokens: u32,
    /// Completion tokens
    pub completion_tokens: u32,
    /// Total tokens
    pub total_tokens: u32,
}

/// Streaming response chunk (for SSE)
#[derive(Debug, Serialize, Deserialize)]
pub struct ChatCompletionChunk {
    /// ID
    pub id: String,
    /// Object
    pub object: String,
    /// Created
    pub created: i64,
    /// Model
    pub model: String,
    /// Choices
    pub choices: Vec<ChunkChoice>,
}

/// Chunk choice structure
#[derive(Debug, Serialize, Deserialize)]
pub struct ChunkChoice {
    /// Index
    pub index: u32,
    /// Delta
    pub delta: Delta,
    /// Finish reason
    pub finish_reason: Option<String>,
}

/// Delta structure
#[derive(Debug, Serialize, Deserialize)]
pub struct Delta {
    #[serde(skip_serializing_if = "Option::is_none")]
    /// Role
    pub role: Option<String>,
    /// Content
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    /// Tool calls
    #[serde(skip_serializing_if = "Option::is_none")]
    /// Tool calls
    pub tool_calls: Option<Vec<ToolCall>>,
}

/// Models list response
#[derive(Debug, Serialize, Deserialize)]
pub struct ModelsResponse {
    /// Object type
    pub object: String,
    /// List of models
    pub data: Vec<Model>,
}

/// Model structure
#[derive(Debug, Serialize, Deserialize)]
pub struct Model {
    /// Model ID
    pub id: String,
    /// Object type
    pub object: String,
    /// Creation timestamp
    pub created: i64,
    /// Owner of the model
    pub owned_by: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Test ChatCompletionRequest serialization/deserialization
    #[test]
    fn test_chat_completion_request_serde() {
        let request = ChatCompletionRequest {
            model: "gpt-4".to_string(),
            messages: vec![Message {
                role: "user".to_string(),
                content: "Hello".to_string(),
                name: None,
                tool_calls: None,
            }],
            temperature: Some(0.8),
            top_p: None,
            n: None,
            stream: Some(false),
            stop: None,
            max_tokens: Some(1000),
            presence_penalty: None,
            frequency_penalty: None,
            user: None,
            tools: None,
            tool_choice: None,
            extra: std::collections::HashMap::new(),
        };

        // Serialize
        let json_str = serde_json::to_string(&request).unwrap();

        // Deserialize
        let deserialized: ChatCompletionRequest = serde_json::from_str(&json_str).unwrap();

        assert_eq!(deserialized.model, "gpt-4");
        assert_eq!(deserialized.messages.len(), 1);
        assert_eq!(deserialized.temperature, Some(0.8));
        assert_eq!(deserialized.max_tokens, Some(1000));
    }

    /// Test ChatCompletionRequest with extra fields
    #[test]
    fn test_chat_completion_request_with_extra_fields() {
        use serde_json::json;

        let json_data = json!({
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "custom_field": "custom_value",
            "another_field": 123
        });

        let request: ChatCompletionRequest = serde_json::from_value(json_data).unwrap();

        assert_eq!(request.model, "gpt-4");
        assert_eq!(request.messages.len(), 1);
        assert!(request.extra.contains_key("custom_field"));
        assert_eq!(
            request.extra.get("custom_field").unwrap().as_str(),
            Some("custom_value")
        );
    }

    /// Test Message with name field
    #[test]
    fn test_message_with_name() {
        let msg = Message {
            role: "user".to_string(),
            content: "Hello".to_string(),
            name: Some("John".to_string()),
            tool_calls: None,
        };

        let json_str = serde_json::to_string(&msg).unwrap();
        assert!(json_str.contains("name"));

        let deserialized: Message = serde_json::from_str(&json_str).unwrap();
        assert_eq!(deserialized.name, Some("John".to_string()));
    }

    /// Test Message without name field (should be omitted in JSON)
    #[test]
    fn test_message_without_name() {
        let msg = Message {
            role: "assistant".to_string(),
            content: "Hi there".to_string(),
            name: None,
            tool_calls: None,
        };

        let json_str = serde_json::to_string(&msg).unwrap();
        assert!(!json_str.contains("name"));
    }

    // ============================================================================
    // Additional Tests for ChatCompletionResponse
    // ============================================================================

    #[test]
    fn test_chat_completion_response_serde() {
        let response = ChatCompletionResponse {
            id: "chatcmpl-123".to_string(),
            object: "chat.completion".to_string(),
            created: 1234567890,
            model: "test-model".to_string(),
            choices: vec![Choice {
                index: 0,
                message: Message {
                    role: "assistant".to_string(),
                    content: "Hello!".to_string(),
                    name: None,
                    tool_calls: None,
                },
                finish_reason: Some("stop".to_string()),
            }],
            usage: Usage {
                prompt_tokens: 10,
                completion_tokens: 20,
                total_tokens: 30,
            },
        };

        // Serialize and deserialize
        let json_str = serde_json::to_string(&response).unwrap();
        let deserialized: ChatCompletionResponse = serde_json::from_str(&json_str).unwrap();

        assert_eq!(deserialized.id, "chatcmpl-123");
        assert_eq!(deserialized.model, "test-model");
        assert_eq!(deserialized.choices.len(), 1);
        assert_eq!(deserialized.usage.total_tokens, 30);
    }

    #[test]
    fn test_chat_completion_response_multiple_choices() {
        let response = ChatCompletionResponse {
            id: "chatcmpl-456".to_string(),
            object: "chat.completion".to_string(),
            created: 1234567890,
            model: "test-model".to_string(),
            choices: vec![
                Choice {
                    index: 0,
                    message: Message {
                        role: "assistant".to_string(),
                        content: "First choice".to_string(),
                        name: None,
                        tool_calls: None,
                    },
                    finish_reason: Some("stop".to_string()),
                },
                Choice {
                    index: 1,
                    message: Message {
                        role: "assistant".to_string(),
                        content: "Second choice".to_string(),
                        name: None,
                        tool_calls: None,
                    },
                    finish_reason: Some("stop".to_string()),
                },
            ],
            usage: Usage {
                prompt_tokens: 10,
                completion_tokens: 40,
                total_tokens: 50,
            },
        };

        assert_eq!(response.choices.len(), 2);
        assert_eq!(response.choices[0].index, 0);
        assert_eq!(response.choices[1].index, 1);
    }

    // ============================================================================
    // Tests for ChatCompletionChunk (streaming)
    // ============================================================================

    #[test]
    fn test_chat_completion_chunk_serde() {
        let chunk = ChatCompletionChunk {
            id: "chatcmpl-stream-1".to_string(),
            object: "chat.completion.chunk".to_string(),
            created: 1234567890,
            model: "test-model".to_string(),
            choices: vec![ChunkChoice {
                index: 0,
                delta: Delta {
                    role: Some("assistant".to_string()),
                    content: None,
                    tool_calls: None,
                },
                finish_reason: None,
            }],
        };

        let json_str = serde_json::to_string(&chunk).unwrap();
        let deserialized: ChatCompletionChunk = serde_json::from_str(&json_str).unwrap();

        assert_eq!(deserialized.id, "chatcmpl-stream-1");
        assert_eq!(deserialized.object, "chat.completion.chunk");
    }

    #[test]
    fn test_chunk_choice_with_content() {
        let choice = ChunkChoice {
            index: 0,
            delta: Delta {
                role: None,
                content: Some("Hello ".to_string()),
                tool_calls: None,
            },
            finish_reason: None,
        };

        let json_str = serde_json::to_string(&choice).unwrap();
        assert!(json_str.contains("Hello "));
    }

    #[test]
    fn test_chunk_choice_with_finish_reason() {
        let choice = ChunkChoice {
            index: 0,
            delta: Delta {
                role: None,
                content: None,
                tool_calls: None,
            },
            finish_reason: Some("stop".to_string()),
        };

        let json_str = serde_json::to_string(&choice).unwrap();
        assert!(json_str.contains("stop"));
    }

    // ============================================================================
    // Tests for Delta
    // ============================================================================

    #[test]
    fn test_delta_with_role_only() {
        let delta = Delta {
            role: Some("assistant".to_string()),
            content: None,
            tool_calls: None,
        };

        let json_str = serde_json::to_string(&delta).unwrap();
        assert!(json_str.contains("assistant"));
        // Should not contain content or tool_calls
        assert!(!json_str.contains("\"content\""));
    }

    #[test]
    fn test_delta_with_content_only() {
        let delta = Delta {
            role: None,
            content: Some("world".to_string()),
            tool_calls: None,
        };

        let json_str = serde_json::to_string(&delta).unwrap();
        assert!(json_str.contains("world"));
        // Should not contain role
        assert!(!json_str.contains("\"role\""));
    }

    #[test]
    fn test_delta_empty() {
        let delta = Delta {
            role: None,
            content: None,
            tool_calls: None,
        };

        let json_str = serde_json::to_string(&delta).unwrap();
        // Empty delta should serialize to mostly empty object
        assert!(!json_str.contains("\"role\""));
        assert!(!json_str.contains("\"content\""));
    }

    // ============================================================================
    // Tests for ModelsResponse
    // ============================================================================

    #[test]
    fn test_models_response_serde() {
        let response = ModelsResponse {
            object: "list".to_string(),
            data: vec![
                Model {
                    id: "model-1".to_string(),
                    object: "model".to_string(),
                    created: 1234567890,
                    owned_by: "org-1".to_string(),
                },
                Model {
                    id: "model-2".to_string(),
                    object: "model".to_string(),
                    created: 1234567891,
                    owned_by: "org-2".to_string(),
                },
            ],
        };

        let json_str = serde_json::to_string(&response).unwrap();
        let deserialized: ModelsResponse = serde_json::from_str(&json_str).unwrap();

        assert_eq!(deserialized.object, "list");
        assert_eq!(deserialized.data.len(), 2);
        assert_eq!(deserialized.data[0].id, "model-1");
        assert_eq!(deserialized.data[1].id, "model-2");
    }

    #[test]
    fn test_models_response_empty_list() {
        let response = ModelsResponse {
            object: "list".to_string(),
            data: vec![],
        };

        let json_str = serde_json::to_string(&response).unwrap();
        let deserialized: ModelsResponse = serde_json::from_str(&json_str).unwrap();

        assert_eq!(deserialized.data.len(), 0);
    }

    // ============================================================================
    // Tests for Model
    // ============================================================================

    #[test]
    fn test_model_serde() {
        let model = Model {
            id: "gpt-4".to_string(),
            object: "model".to_string(),
            created: 1234567890,
            owned_by: "openai".to_string(),
        };

        let json_str = serde_json::to_string(&model).unwrap();
        let deserialized: Model = serde_json::from_str(&json_str).unwrap();

        assert_eq!(deserialized.id, "gpt-4");
        assert_eq!(deserialized.object, "model");
        assert_eq!(deserialized.created, 1234567890);
        assert_eq!(deserialized.owned_by, "openai");
    }

    // ============================================================================
    // Tests for Usage
    // ============================================================================

    #[test]
    fn test_usage_serde() {
        let usage = Usage {
            prompt_tokens: 50,
            completion_tokens: 100,
            total_tokens: 150,
        };

        let json_str = serde_json::to_string(&usage).unwrap();
        let deserialized: Usage = serde_json::from_str(&json_str).unwrap();

        assert_eq!(deserialized.prompt_tokens, 50);
        assert_eq!(deserialized.completion_tokens, 100);
        assert_eq!(deserialized.total_tokens, 150);
    }

    #[test]
    fn test_usage_zero_tokens() {
        let usage = Usage {
            prompt_tokens: 0,
            completion_tokens: 0,
            total_tokens: 0,
        };

        let json_str = serde_json::to_string(&usage).unwrap();
        let deserialized: Usage = serde_json::from_str(&json_str).unwrap();

        assert_eq!(deserialized.total_tokens, 0);
    }

    // ============================================================================
    // Tests for Choice
    // ============================================================================

    #[test]
    fn test_choice_serde() {
        let choice = Choice {
            index: 0,
            message: Message {
                role: "assistant".to_string(),
                content: "Test response".to_string(),
                name: None,
                tool_calls: None,
            },
            finish_reason: Some("stop".to_string()),
        };

        let json_str = serde_json::to_string(&choice).unwrap();
        let deserialized: Choice = serde_json::from_str(&json_str).unwrap();

        assert_eq!(deserialized.index, 0);
        assert_eq!(deserialized.message.content, "Test response");
        assert_eq!(deserialized.finish_reason, Some("stop".to_string()));
    }

    #[test]
    fn test_choice_no_finish_reason() {
        let choice = Choice {
            index: 0,
            message: Message {
                role: "assistant".to_string(),
                content: "Partial response".to_string(),
                name: None,
                tool_calls: None,
            },
            finish_reason: None,
        };

        assert!(choice.finish_reason.is_none());
    }

    // ============================================================================
    // Tests for Tool and ToolCall
    // ============================================================================

    #[test]
    fn test_tool_serde() {
        use serde_json::json;

        let tool = Tool {
            tool_type: "function".to_string(),
            function: FunctionDefinition {
                name: "get_weather".to_string(),
                description: Some("Get the weather".to_string()),
                parameters: json!({
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    }
                }),
            },
        };

        let json_str = serde_json::to_string(&tool).unwrap();
        let deserialized: Tool = serde_json::from_str(&json_str).unwrap();

        assert_eq!(deserialized.tool_type, "function");
        assert_eq!(deserialized.function.name, "get_weather");
    }

    #[test]
    fn test_tool_call_serde() {
        let tool_call = ToolCall {
            id: "call_123".to_string(),
            call_type: "function".to_string(),
            function: FunctionCall {
                name: "get_weather".to_string(),
                arguments: r#"{"location": "San Francisco"}"#.to_string(),
            },
        };

        let json_str = serde_json::to_string(&tool_call).unwrap();
        let deserialized: ToolCall = serde_json::from_str(&json_str).unwrap();

        assert_eq!(deserialized.id, "call_123");
        assert_eq!(deserialized.function.name, "get_weather");
    }

    // ============================================================================
    // Tests for FunctionDefinition
    // ============================================================================

    #[test]
    fn test_function_definition_with_description() {
        use serde_json::json;

        let func_def = FunctionDefinition {
            name: "test_func".to_string(),
            description: Some("A test function".to_string()),
            parameters: json!({"type": "object"}),
        };

        let json_str = serde_json::to_string(&func_def).unwrap();
        assert!(json_str.contains("test_func"));
        assert!(json_str.contains("A test function"));
    }

    #[test]
    fn test_function_definition_without_description() {
        use serde_json::json;

        let func_def = FunctionDefinition {
            name: "test_func".to_string(),
            description: None,
            parameters: json!({"type": "object"}),
        };

        let json_str = serde_json::to_string(&func_def).unwrap();
        assert!(json_str.contains("test_func"));
        // Description should not be in JSON when None
        assert!(!json_str.contains("\"description\""));
    }

    // ============================================================================
    // Tests for FunctionCall
    // ============================================================================

    #[test]
    fn test_function_call_serde() {
        let func_call = FunctionCall {
            name: "calculate".to_string(),
            arguments: r#"{"x": 5, "y": 10}"#.to_string(),
        };

        let json_str = serde_json::to_string(&func_call).unwrap();
        let deserialized: FunctionCall = serde_json::from_str(&json_str).unwrap();

        assert_eq!(deserialized.name, "calculate");
        assert!(deserialized.arguments.contains("5"));
    }

    // ============================================================================
    // Tests for Request Parameters
    // ============================================================================

    #[test]
    fn test_request_with_temperature() {
        let request = ChatCompletionRequest {
            model: "gpt-4".to_string(),
            messages: vec![],
            temperature: Some(0.7),
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
            extra: std::collections::HashMap::new(),
        };

        assert_eq!(request.temperature, Some(0.7));
    }

    #[test]
    fn test_request_with_all_optional_params() {
        use serde_json::json;

        let request = ChatCompletionRequest {
            model: "gpt-4".to_string(),
            messages: vec![],
            temperature: Some(0.8),
            top_p: Some(0.9),
            n: Some(1),
            stream: Some(true),
            stop: Some(vec!["STOP".to_string()]),
            max_tokens: Some(2000),
            presence_penalty: Some(0.5),
            frequency_penalty: Some(0.5),
            user: Some("user123".to_string()),
            tools: Some(vec![]),
            tool_choice: Some(json!("auto")),
            extra: std::collections::HashMap::new(),
        };

        assert!(request.temperature.is_some());
        assert!(request.top_p.is_some());
        assert!(request.n.is_some());
        assert!(request.stream.is_some());
        assert!(request.stop.is_some());
        assert!(request.max_tokens.is_some());
        assert!(request.presence_penalty.is_some());
        assert!(request.frequency_penalty.is_some());
        assert!(request.user.is_some());
    }
}
