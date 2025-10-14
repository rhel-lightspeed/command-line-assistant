# Command Line Assistant (CLA) Architecture

This document provides a comprehensive overview of the Command Line Assistant codebase architecture.

## System Architecture Diagram

```mermaid
flowchart TB
 subgraph subGraph0["User Interface Layer"]
        USER["User Terminal"]
  end
 subgraph subGraph1["CLI Crate (c binary)"]
        CLI_MAIN["cli/main.rs<br>Argument Router"]
        CLI_CHAT["commands/chat.rs"]
        CLI_HISTORY["commands/history.rs"]
        CLI_SHELL["commands/shell.rs"]
        CLI_HELPERS["helpers.rs<br>Config &amp; Validation"]
        CLI_CONFIG["config.rs"]
  end
 subgraph subGraph2["CLI Integration"]
        CLI["CLI Binary<br>/usr/bin/<cli><br>AI Assistant Framework"]
  end
 subgraph subGraph3["CLAD Daemon (clad binary)"]
        CLAD_MAIN["clad/main.rs<br>API Server"]
        CLAD_ROUTER["Router<br>Axum Framework"]
        CLAD_PROVIDER["provider.rs<br>Request Handler"]
        CLAD_OPENAI["openai.rs<br>OpenAI Request/Response format"]
        CLAD_CONFIG["config.rs<br>Configuration"]
        CLAD_STATE["state.rs<br>App State"]
  end
 subgraph subGraph4["External Backend"]
        BACKEND["Red Hat Lightspeed<br>AI Backend Service"]
  end
    CLI_MAIN -- routes to --> CLI_CHAT & CLI_HISTORY & CLI_SHELL
    CLI_CHAT -- uses --> CLI_HELPERS
    CLI_HELPERS -- manages --> CLI_CONFIG
    CLAD_MAIN -- creates --> CLAD_ROUTER & CLAD_STATE
    CLAD_ROUTER -- /v1/chat/completions --> CLAD_PROVIDER
    CLAD_ROUTER -- /v1/models --> CLAD_PROVIDER
    CLAD_ROUTER -- /health --> CLAD_PROVIDER
    CLAD_PROVIDER -- uses --> CLAD_OPENAI
    CLAD_PROVIDER -- transforms --> CLAD_OPENAI
    CLAD_MAIN -- loads --> CLAD_CONFIG
    USER -- c 'query' --> CLI_MAIN
    USER -- "c chat -i" --> CLI_MAIN
    USER -- c history --> CLI_MAIN
    CLI_CHAT -- spawns process --> CLI
    CLI -- "HTTP: OpenAI API format<br>127.0.0.1:8080" --> CLAD_ROUTER
    CLAD_PROVIDER -- HTTP: Lightspeed format<br>Certificate Auth --> BACKEND
    BACKEND -- JSON response --> CLAD_PROVIDER
    CLAD_PROVIDER -- OpenAI format --> CLI
    CLI -- formatted output --> USER

    style USER fill:#e1f5ff
    style CLI_MAIN fill:#f0e1ff
    style CLI fill:#fff4e1
    style CLAD_MAIN fill:#e1ffe1
    style BACKEND fill:#ffe1e1
```

## Component Details

### 1. CLI Crate (`c` binary)

**Purpose**: User-facing command-line interface for quick AI assistance

**Key Components**:
- **main.rs**: Smart argument routing
  - Defaults to chat mode for natural language
  - Routes to specific subcommands (chat, history, shell)
  - Handles special cases like `-i` for interactive mode

- **commands/chat.rs**: Chat command implementation
  - Interactive mode: `c -i` → spawns `cli session`
  - Query mode: `c "question"` → spawns `cli run -t "question"`
  - Validates arguments and finds cli binary

- **commands/history.rs**: History management (stub)
  - View past conversations
  - List with filters and limits

- **commands/shell.rs**: Shell integration (stub)
  - Install/uninstall shell hooks
  - Shell-specific integrations (bash, zsh, fish)

- **helpers.rs**: Utility functions
  - Find cli binary (`/usr/bin/cli` or `$CLI_BINARY`)
  - Validate arguments (security checks)
  - Manage cli config files
  - Environment variable filtering

- **config.rs**: Configuration management
  - Manages cli configuration at `~/.config/cli/`
  - Creates `config.yaml` with CLAD endpoint

### 2. CLAD Daemon (`clad` binary)

**Purpose**: OpenAI-compatible API proxy to Red Hat Lightspeed backend

**Key Components**:
- **main.rs**: Axum web server
  - Listens on `127.0.0.1:8080` (fixed)
  - Creates authenticated HTTP client
  - Routes requests to handlers

- **provider.rs**: Request/response transformation
  - Transforms OpenAI chat format → Red Hat Lightspeed format
  - Transforms Lightspeed responses → OpenAI format
  - Handles streaming and non-streaming responses
  - Adds system context (OS info, machine ID)

- **openai.rs**: OpenAI API data structures
  - ChatCompletionRequest/Response
  - Message, Choice, Usage models
  - Streaming chunk models

- **config.rs**: Configuration loading
  - Backend endpoint URL
  - Certificate/key file paths for auth
  - Proxy settings (HTTP/HTTPS)
  - Logging level

- **state.rs**: Application state
  - Shared state across handlers
  - Config and HTTP client

### 3. CLI Integration

**Purpose**: AI assistant framework that connects to CLAD

**Role**:
- Manages conversation sessions
- Handles tool calling and extensions
- Formats output for terminal display
- Connects to CLAD via OpenAI-compatible API

**Configuration**: Created by CLI at `~/.config/cli/config.yaml`
```yaml
OLLAMA_HOST: 127.0.0.1:8080
CLI_MODEL: default-model
CLI_PROVIDER: ollama
```

### 4. External Backend

**Red Hat Lightspeed Backend**:
- AI inference service
- Requires certificate-based authentication
- Custom request/response format:
  - Request: `{"question": "...", "context": {...}}`
  - Response: `{"data": {"text": "..."}}`

## Data Flow

### Chat Query Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as c (CLI)
    participant Cli
    participant CLAD as clad (Daemon)
    participant Backend as Lightspeed Backend

    User->>CLI: c "how do I list files?"
    CLI->>CLI: Route to chat command
    CLI->>CLI: Find cli binary
    CLI->>CLI: Ensure config files exist
    CLI->>Cli: spawn: cli run -t "how do I list files?"

    Cli->>CLAD: POST /v1/chat/completions<br/>(OpenAI format)
    Note over CLAD: Transform request
    CLAD->>Backend: POST endpoint<br/>(Lightspeed format + system context)
    Backend-->>CLAD: JSON response<br/>{"data": {"text": "..."}}
    Note over CLAD: Transform response
    CLAD-->>Cli: OpenAI format response
    Cli-->>User: Formatted AI response
```

### Interactive Session Flow

```mermaid
sequenceDiagram
  participant User as User
  participant CLI as c (CLI)
  participant Cli as Cli
  participant CLAD as clad (Daemon)
  participant Backend as Lightspeed Backend

  User ->> CLI: c -i/--interactive
  CLI ->> Cli: spawn: cli session
  Cli ->> User: Interactive prompt
  loop Chat Session
    User ->> Cli: Enter message
    Cli ->> CLAD: POST /v1/chat/completions
    CLAD ->> Backend: POST with context
    Backend -->> CLAD: Response
    CLAD -->> Cli: OpenAI format
    Cli -->> User: Display response
  end
  User ->> Cli: exit
  Cli -->> CLI: Exit code
  CLI -->> User: Return to shell
```

### Request Transformation

```mermaid
graph LR
    subgraph "OpenAI Format (Cli → CLAD)"
        OAI["{<br/>  messages: [{<br/>    role: 'user',<br/>    content: '...'<br/>  }],<br/>  model: 'default-model',<br/>  stream: false<br/>}"]
    end

    subgraph "CLAD Transformation"
        TRANSFORM[Extract last user message<br/>+ Add system context]
    end

    subgraph "Lightspeed Format (CLAD → Backend)"
        LS["{<br/>  question: '...',<br/>  context: {<br/>    systeminfo: {...},<br/>    terminal: {...},<br/>    cla: {version}<br/>  }<br/>}"]
    end

    OAI -->|provider.rs| TRANSFORM
    TRANSFORM -->|transform_request()| LS
```

## Configuration Files

### CLAD Configuration
**Location**: `/etc/xdg/command-line-assistant/config.toml` (or `$XDG_CONFIG_DIRS`)

```toml
[backend]
endpoint = "https://api.example.com/query"
timeout = 30

[backend.auth]
cert_file = "/etc/pki/consumer/cert.pem"
key_file = "/etc/pki/consumer/key.pem"

[backend.proxies]
http = "http://proxy:8080"
https = "https://proxy:8443"

[logging]
level = "INFO"
```

### Cli Configuration
**Location**: `~/.config/cli/config.yaml`

```yaml
OLLAMA_HOST: 127.0.0.1:8080
CLI_MODEL: default-model
CLI_PROVIDER: ollama
extensions:
  memory:
    enabled: true
    type: builtin
```

## Key Design Decisions

### 1. Smart CLI Routing
The `c` command intelligently routes arguments:
- `c "query"` → chat mode (default)
- `c -i` → interactive chat
- `c history` → history subcommand
- `c history from yesterday` → chat mode (natural language)
- `c history --list` → history subcommand (flag detected)

### 2. API Compatibility Layer
CLAD provides OpenAI-compatible API to:
- Work with existing AI tools (Cli)
- Abstract backend differences
- Enable easy switching between backends

### 3. Security Features
- Certificate-based authentication to backend
- Environment variable filtering
- Argument validation (length limits, null byte checks)
- Atomic file writes with locking

### 4. Streaming Support
CLAD simulates streaming by:
- Getting full response from backend
- Breaking into word-level chunks
- Sending as SSE events to client

### 5. Context Enrichment
Every request includes:
- OS information
- System version
- Architecture
- Machine ID
- CLA version

## Development Tools

### xtask Crate
**Purpose**: Build tooling for the workspace

**Key Functions**:
- Generate man pages from CLI structure
- Documentation generation
- Build automation

## Deployment Architecture

```mermaid
flowchart TB
    subgraph "User Machine"
        CLI_BIN["/usr/bin/c"]
        CLAD_BIN["/usr/bin/clad"]
        CLAD_SERVICE["systemd service: clad.service"]
        CONFIG["/etc/xdg/command-line-assistant/config.toml"]
        CLI_BIN["/usr/bin/cli"]

        CLI_BIN -.->|spawns| CLI_BIN
        CLI_BIN -->|HTTP| CLAD_SERVICE
        CLAD_SERVICE -->|reads| CONFIG
        CLAD_BIN -->|runs as| CLAD_SERVICE
    end

    subgraph "Network"
        PROXY["Corporate Proxy"]
    end

    subgraph "Red Hat Services"
        BACKEND["Lightspeed Backend"]
    end

    CLAD_SERVICE -->|via proxy| PROXY
    PROXY --> BACKEND
    CLAD_SERVICE -.->|cert auth| BACKEND

    style CLI_BIN fill:#f0e1ff
    style CLAD_SERVICE fill:#e1ffe1
    style BACKEND fill:#ffe1e1
```

## API Endpoints

### CLAD Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/v1/chat/completions` | POST | Chat completions (OpenAI-compatible) |
| `/v1/models` | GET | List available models |

## Error Handling

### Exit Codes (CLI)
- `69` (EX_UNAVAILABLE): Cli binary not found
- `70` (EX_SOFTWARE): Internal software error
- `71` (EX_OSERR): System error
- `73` (EX_CANTCREAT): Can't create output file

### Error Responses (CLAD)
- `502 Bad Gateway`: Backend service unavailable
- `500 Internal Server Error`: Transform/internal error
- `504 Gateway Timeout`: Request timeout

## Testing

### Test Coverage
- Unit tests for all core functions
- Integration tests for API endpoints
- Security tests for argument validation
- Concurrency tests for config file operations

### Key Test Areas
1. **CLI Routing Logic**: Extensive tests for argument parsing
2. **Request Transformation**: OpenAI ↔ Lightspeed format
3. **Security**: Argument validation, null bytes, length limits
4. **Concurrency**: Atomic writes, file locking
5. **Streaming**: SSE event generation

## Future Enhancements

### Planned Features
1. **History Command**: Full implementation with database
2. **Shell Integration**: Bash/Zsh/Fish hooks
3. **Multiple Backends**: Support for additional AI providers
4. **Advanced Caching**: Response caching layer
5. **Telemetry**: Usage metrics and analytics

---

# Code Structure Diagrams

## Workspace and Crate Structure

```mermaid
graph TB
    subgraph "Cargo Workspace"
        WORKSPACE[Cargo.toml<br/>Workspace Root]

        subgraph "CLI Crate (c binary)"
            CLI_PKG[Cargo.toml<br/>name: c<br/>bin: /usr/bin/c]
            CLI_MAIN[main.rs<br/>Entry Point<br/>CLI Parser]
            CLI_MOD_CMD[commands/mod.rs]
            CLI_CHAT[commands/chat.rs<br/>ChatArgs]
            CLI_HISTORY[commands/history.rs<br/>HistoryArgs]
            CLI_SHELL[commands/shell.rs<br/>ShellArgs]
            CLI_CONFIG[config.rs<br/>APP_STRATEGY]
            CLI_HELPERS[helpers.rs<br/>Utilities]
            CLI_JSON[cli_json.rs<br/>feature: docgen]

            CLI_PKG --> CLI_MAIN
            CLI_MAIN --> CLI_MOD_CMD
            CLI_MAIN --> CLI_CONFIG
            CLI_MAIN --> CLI_JSON
            CLI_MOD_CMD --> CLI_CHAT
            CLI_MOD_CMD --> CLI_HISTORY
            CLI_MOD_CMD --> CLI_SHELL
            CLI_CHAT --> CLI_HELPERS
            CLI_HELPERS --> CLI_CONFIG
        end

        subgraph "CLAD Crate (clad binary)"
            CLAD_PKG[Cargo.toml<br/>name: clad<br/>bin: /usr/bin/clad]
            CLAD_MAIN[main.rs<br/>Axum Server<br/>Entry Point]
            CLAD_PROVIDER[provider.rs<br/>HTTP Handlers<br/>Transformations]
            CLAD_OPENAI[openai.rs<br/>OpenAI Models]
            CLAD_CONFIG[config.rs<br/>Config Structs]
            CLAD_STATE[state.rs<br/>AppState]

            CLAD_PKG --> CLAD_MAIN
            CLAD_MAIN --> CLAD_PROVIDER
            CLAD_MAIN --> CLAD_CONFIG
            CLAD_MAIN --> CLAD_STATE
            CLAD_PROVIDER --> CLAD_OPENAI
            CLAD_PROVIDER --> CLAD_STATE
            CLAD_STATE --> CLAD_CONFIG
        end

        subgraph "XTask Crate (build tool)"
            XTASK_PKG[Cargo.toml<br/>name: xtask]
            XTASK_MAIN[xtask.rs<br/>Build Commands]
            XTASK_MAN[man.rs<br/>Man Page Generator]

            XTASK_PKG --> XTASK_MAIN
            XTASK_MAIN --> XTASK_MAN
        end

        WORKSPACE --> CLI_PKG
        WORKSPACE --> CLAD_PKG
        WORKSPACE --> XTASK_PKG
    end

    style CLI_PKG fill:#f0e1ff
    style CLAD_PKG fill:#e1ffe1
    style XTASK_PKG fill:#ffe1e1
```

## CLI Crate Module Dependencies

```mermaid
graph LR
    subgraph "External Dependencies"
        CLAP[clap<br/>CLI Parser]
        ETCETERA[etcetera<br/>App Directories]
        FS2[fs2<br/>File Locking]
        LOG[log + env_logger<br/>Logging]
        ANYHOW[anyhow<br/>Error Handling]
        SERDE[serde + serde_json<br/>Serialization]
    end

    subgraph "CLI Module Structure"
        MAIN[main.rs<br/>--<br/>Cli struct<br/>Commands enum<br/>should_route_to_chat]

        CONFIG[config.rs<br/>--<br/>APP_STRATEGY]

        HELPERS[helpers.rs<br/>--<br/>find_cli_binary<br/>validate_args<br/>ensure_cli_config_files<br/>atomic_write<br/>get_filtered_env<br/>is_executable]

        COMMANDS[commands/mod.rs<br/>--<br/>pub mod chat<br/>pub mod history<br/>pub mod shell]

        CHAT[commands/chat.rs<br/>--<br/>ChatArgs struct<br/>execute()<br/>run_cli()]

        HISTORY[commands/history.rs<br/>--<br/>HistoryArgs struct<br/>execute()]

        SHELL[commands/shell.rs<br/>--<br/>ShellArgs struct<br/>execute()]

        DOCGEN[cli_json.rs<br/>feature: docgen<br/>--<br/>dump_cli_json]
    end

    MAIN -->|uses| COMMANDS
    MAIN -->|uses| CLAP
    MAIN -->|uses| LOG
    MAIN -.->|feature: docgen| DOCGEN

    COMMANDS -->|re-exports| CHAT
    COMMANDS -->|re-exports| HISTORY
    COMMANDS -->|re-exports| SHELL

    CHAT -->|uses| HELPERS
    CHAT -->|uses| CLAP
    CHAT -->|uses| LOG

    HELPERS -->|uses| CONFIG
    HELPERS -->|uses| ETCETERA
    HELPERS -->|uses| FS2
    HELPERS -->|uses| ANYHOW
    HELPERS -->|uses| LOG

    CONFIG -->|uses| ETCETERA

    DOCGEN -->|uses| CLAP
    DOCGEN -->|uses| SERDE

    style MAIN fill:#f0e1ff
    style HELPERS fill:#e8d4ff
    style CONFIG fill:#e8d4ff
```

## CLAD Crate Module Dependencies

```mermaid
graph LR
    subgraph "External Dependencies"
        AXUM[axum<br/>Web Framework]
        TOKIO[tokio<br/>Async Runtime]
        REQWEST[reqwest<br/>HTTP Client]
        SERDE_EXT[serde + serde_json<br/>Serialization]
        TOML[toml<br/>Config Parsing]
        TRACING[tracing<br/>Logging]
        UUID[uuid<br/>ID Generation]
        THISERROR[thiserror<br/>Errors]
    end

    subgraph "CLAD Module Structure"
        MAIN_D[main.rs<br/>--<br/>tokio::main<br/>create Router<br/>load Config<br/>bind server]

        PROVIDER[provider.rs<br/>--<br/>chat_completions_handler<br/>models_handler<br/>health_check_handler<br/>create_authenticated_client<br/>transform_request<br/>transform_response<br/>AppError enum]

        OPENAI[openai.rs<br/>--<br/>ChatCompletionRequest<br/>ChatCompletionResponse<br/>Message, Choice, Usage<br/>ChatCompletionChunk<br/>Tool, ToolCall<br/>ModelsResponse, Model]

        CONFIG_D[config.rs<br/>--<br/>Config struct<br/>BackendConfig<br/>AuthConfig<br/>LoggingConfig<br/>from_file()]

        STATE_D[state.rs<br/>--<br/>AppState struct<br/>config: Arc&lt;Config&gt;<br/>client: reqwest::Client]
    end

    MAIN_D -->|uses| PROVIDER
    MAIN_D -->|uses| CONFIG_D
    MAIN_D -->|uses| STATE_D
    MAIN_D -->|uses| AXUM
    MAIN_D -->|uses| TOKIO
    MAIN_D -->|uses| TRACING

    PROVIDER -->|uses| STATE_D
    PROVIDER -->|uses| OPENAI
    PROVIDER -->|uses| CONFIG_D
    PROVIDER -->|uses| AXUM
    PROVIDER -->|uses| REQWEST
    PROVIDER -->|uses| SERDE_EXT
    PROVIDER -->|uses| UUID
    PROVIDER -->|uses| THISERROR

    STATE_D -->|contains| CONFIG_D
    STATE_D -->|contains| REQWEST

    CONFIG_D -->|uses| SERDE_EXT
    CONFIG_D -->|uses| TOML

    OPENAI -->|uses| SERDE_EXT

    style MAIN_D fill:#e1ffe1
    style PROVIDER fill:#d4ffe8
    style OPENAI fill:#d4ffe8
```

## Key Data Structures and Their Relationships

```mermaid
classDiagram
    class Cli {
        +Option~Commands~ command
        +execute()
    }

    class Commands {
        <<enum>>
        Chat(ChatArgs)
        History(HistoryArgs)
        Shell(ShellArgs)
        Internals
    }

    class ChatArgs {
        +bool interactive
        +Vec~String~ query
        +execute()
        -execute_interactive()
        -execute_query()
        +build_interactive_args()
        +build_query_args()
    }

    class HistoryArgs {
        +bool list
        +bool verbose
        +usize limit
        +execute()
    }

    class ShellArgs {
        +bool install
        +bool uninstall
        +bool status
        +Option~String~ shell_type
        +execute()
    }

    class Config {
        +BackendConfig backend
        +LoggingConfig logging
        +Option~DatabaseConfig~ database
        +Option~HistoryConfig~ history
        +from_file()
        +get_tracing_filter()
    }

    class BackendConfig {
        +String endpoint
        +u64 timeout
        +Option~HashMap~ proxies
        +AuthConfig auth
    }

    class AuthConfig {
        +String cert_file
        +String key_file
    }

    class AppState {
        +Arc~Config~ config
        +reqwest::Client client
    }

    class ChatCompletionRequest {
        +String model
        +Vec~Message~ messages
        +Option~bool~ stream
        +Option~Vec~Tool~~ tools
    }

    class ChatCompletionResponse {
        +String id
        +String model
        +Vec~Choice~ choices
        +Usage usage
    }

    class Message {
        +String role
        +String content
        +Option~String~ name
        +Option~Vec~ToolCall~~ tool_calls
    }

    class Choice {
        +u32 index
        +Message message
        +Option~String~ finish_reason
    }

    class Usage {
        +u32 prompt_tokens
        +u32 completion_tokens
        +u32 total_tokens
    }

    Cli --> Commands
    Commands --> ChatArgs
    Commands --> HistoryArgs
    Commands --> ShellArgs

    Config --> BackendConfig
    BackendConfig --> AuthConfig
    AppState --> Config

    ChatCompletionRequest --> Message
    ChatCompletionRequest --> Tool
    ChatCompletionResponse --> Choice
    ChatCompletionResponse --> Usage
    Choice --> Message
    Message --> ToolCall

    note for Cli "CLI Entry Point\nRoutes commands"
    note for Config "CLAD Configuration\nLoaded from TOML"
    note for AppState "Shared handler state"
    note for ChatCompletionRequest "OpenAI-compatible\nrequest format"
```

## File Import Graph - CLI Crate

```mermaid
graph TD
    MAIN_CLI["main.rs<br/>==========<br/>mod commands<br/>mod config<br/>mod helpers<br/>mod cli_json"]

    CMD_MOD["commands/mod.rs<br/>==========<br/>pub mod chat<br/>pub mod history<br/>pub mod shell"]

    CHAT_CMD["commands/chat.rs<br/>==========<br/>use crate::helpers::*<br/>use clap::Args<br/>use log"]

    HIST_CMD["commands/history.rs<br/>==========<br/>use clap::Args"]

    SHELL_CMD["commands/shell.rs<br/>==========<br/>use clap::Args"]

    CONFIG_CLI["config.rs<br/>==========<br/>use etcetera<br/>use once_cell"]

    HELPERS_CLI["helpers.rs<br/>==========<br/>use crate::config<br/>use anyhow<br/>use etcetera<br/>use fs2<br/>use log"]

    MAIN_CLI --> CMD_MOD
    MAIN_CLI --> CONFIG_CLI
    MAIN_CLI --> HELPERS_CLI

    CMD_MOD --> CHAT_CMD
    CMD_MOD --> HIST_CMD
    CMD_MOD --> SHELL_CMD

    CHAT_CMD --> HELPERS_CLI
    HELPERS_CLI --> CONFIG_CLI

    style MAIN_CLI fill:#f0e1ff
    style HELPERS_CLI fill:#e8d4ff
```

## File Import Graph - CLAD Crate

```mermaid
graph TD
    MAIN_CLAD["main.rs<br/>==========<br/>mod config<br/>mod openai<br/>mod provider<br/>mod state<br/>use axum::Router"]

    PROVIDER_D["provider.rs<br/>==========<br/>use crate::config::Config<br/>use crate::openai::*<br/>use crate::state::AppState<br/>use axum<br/>use reqwest<br/>use serde_json"]

    OPENAI_D["openai.rs<br/>==========<br/>use serde<br/>use serde_json::Value"]

    CONFIG_CLAD["config.rs<br/>==========<br/>use serde::Deserialize<br/>use toml"]

    STATE_CLAD["state.rs<br/>==========<br/>use crate::config::Config<br/>use std::sync::Arc<br/>use reqwest"]

    MAIN_CLAD --> PROVIDER_D
    MAIN_CLAD --> CONFIG_CLAD
    MAIN_CLAD --> STATE_CLAD
    MAIN_CLAD --> OPENAI_D

    PROVIDER_D --> OPENAI_D
    PROVIDER_D --> CONFIG_CLAD
    PROVIDER_D --> STATE_CLAD

    STATE_CLAD --> CONFIG_CLAD

    style MAIN_CLAD fill:#e1ffe1
    style PROVIDER_D fill:#d4ffe8
```

## Function Call Graph - CLI Execution Flow

```mermaid
graph TD
    START([User runs: c query])

    MAIN_FN[main::main]
    PARSE[Cli::parse]
    ROUTE[should_route_to_chat]
    EXECUTE[Cli::execute]

    CHAT_EXEC[ChatArgs::execute]
    ENSURE_CFG[helpers::ensure_cli_config_files]
    FIND_CLI[helpers::find_cli_binary]
    VALIDATE[helpers::validate_args]
    BUILD_ARGS[ChatArgs::build_query_args]
    RUN[chat::run_cli]

    ATOMIC[helpers::atomic_write]
    FILTER_ENV[helpers::get_filtered_env]

    SPAWN[Command::new.spawn]
    WAIT[child.wait]
    EXIT([exit])

    START --> MAIN_FN
    MAIN_FN --> ROUTE
    ROUTE -->|default to chat| PARSE
    PARSE --> EXECUTE
    EXECUTE --> CHAT_EXEC

    CHAT_EXEC --> ENSURE_CFG
    ENSURE_CFG --> ATOMIC
    CHAT_EXEC --> FIND_CLI_BINARY
    CHAT_EXEC --> VALIDATE
    CHAT_EXEC --> BUILD_ARGS
    CHAT_EXEC --> RUN

    RUN --> FILTER_ENV
    RUN --> SPAWN
    SPAWN --> WAIT
    WAIT --> EXIT

    style START fill:#f0e1ff
    style MAIN_FN fill:#f0e1ff
    style CHAT_EXEC fill:#e8d4ff
    style EXIT fill:#f0e1ff
```

## Function Call Graph - CLAD Request Handling

```mermaid
graph TD
    HTTP_REQ([HTTP Request])

    ROUTER[axum::Router]
    HANDLER[chat_completions_handler]
    STREAM_CHECK{stream?}

    HANDLE_STREAM[handle_streaming_request]
    HANDLE_NORMAL[handle_non_streaming_request]

    TRANSFORM_REQ[transform_request]
    CLIENT_POST[client.post.send]
    TRANSFORM_RESP[transform_response]
    EXTRACT_TEXT[extract_streaming_text]
    CREATE_CHUNKS[create_streaming_chunks]

    BACKEND([Backend API])
    RESPONSE([HTTP Response])

    HTTP_REQ --> ROUTER
    ROUTER --> HANDLER
    HANDLER --> STREAM_CHECK

    STREAM_CHECK -->|false| HANDLE_NORMAL
    STREAM_CHECK -->|true| HANDLE_STREAM

    HANDLE_NORMAL --> TRANSFORM_REQ
    TRANSFORM_REQ --> CLIENT_POST
    CLIENT_POST --> BACKEND
    BACKEND --> TRANSFORM_RESP
    TRANSFORM_RESP --> RESPONSE

    HANDLE_STREAM --> TRANSFORM_REQ
    TRANSFORM_REQ --> CLIENT_POST
    CLIENT_POST --> BACKEND
    BACKEND --> EXTRACT_TEXT
    EXTRACT_TEXT --> CREATE_CHUNKS
    CREATE_CHUNKS --> RESPONSE

    style HTTP_REQ fill:#e1ffe1
    style HANDLER fill:#d4ffe8
    style TRANSFORM_REQ fill:#c8ffd4
    style TRANSFORM_RESP fill:#c8ffd4
    style RESPONSE fill:#e1ffe1
```

## Testing Structure

```mermaid
graph TB
    subgraph "CLI Tests"
        CLI_TESTS[main.rs tests<br/>--<br/>test_should_route_to_chat<br/>test_parse_commands<br/>test_argument_handling]

        CHAT_TESTS[commands/chat.rs tests<br/>--<br/>test_build_args<br/>test_mode_detection]

        HELPER_TESTS[helpers.rs tests<br/>--<br/>test_is_executable<br/>test_find_cli_binary<br/>test_validate_args<br/>test_atomic_write<br/>test_get_filtered_env]

        CONFIG_TESTS[config.rs tests<br/>--<br/>test_app_strategy]
    end

    subgraph "CLAD Tests"
        PROVIDER_TESTS[provider.rs tests<br/>--<br/>test_uuid_simple<br/>test_timestamp<br/>test_app_error<br/>test_streaming_chunks<br/>test_handlers]

        CONFIG_TESTS_D[config.rs tests<br/>--<br/>test_config_deserialization<br/>test_config_with_proxies<br/>test_defaults]

        OPENAI_TESTS[openai.rs tests<br/>--<br/>test_serde<br/>test_extra_fields<br/>test_message_serialization]
    end

    style CLI_TESTS fill:#f0e1ff
    style HELPER_TESTS fill:#e8d4ff
    style PROVIDER_TESTS fill:#e1ffe1
```

---

**Version**: 1.0.0
**Repository**: https://github.com/r0x0d/cla-rust
**License**: See LICENSE file
