# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ComfyUI** is a visual AI engine and application that uses a graph/nodes/flowchart interface for building complex AI pipelines. It supports multiple model types (image generation, video, audio, 3D) and executes workflows through an asynchronous queue system with intelligent caching and memory management.

### Key Technologies
- **Python 3.9+**: Core implementation, Python 3.13 strongly recommended
- **PyTorch**: ML framework with support for NVIDIA, AMD, Intel, and Apple Silicon GPUs
- **aiohttp**: Async web server for REST API and WebSocket communication
- **SQLAlchemy**: Database ORM with Alembic migrations
- **Pydantic**: Data validation with version 2.0+
- **PIL**: Image processing
- **transformers**: For text encoding and model loading

## Architecture Overview

### Core System Structure

**comfy/** - Core AI/ML engine
- `model_management.py`: GPU memory management, model loading/unloading with smart offloading
- `model_sampling.py`: Sampling algorithms and diffusion logic
- `clip_model.py`, `clip_vision.py`: Text and image encoding models
- `latent_formats.py`, `sample.py`: Latent manipulation and sampling
- `ops.py`: PyTorch operations with device placement logic
- **ldm/**: Latent diffusion models (SD1.x, SDXL, Flux, HunyuanDiT, Cascade, etc.)
- **k_diffusion/**: Advanced samplers (DEIS, SA Solver, Uni-PC)
- **weight_adapter/**: LoRA, LoHa, LoKr, BOFT implementation

**comfy_api/** - Public API layer with versioning
- **latest/**: Current stable API (io.py for type definitions)
- `v0_0_1/`, `v0_0_2/`: Legacy API versions
- **internal/**: Private node registration and metadata (`_ComfyNodeInternal`)
- `feature_flags.py`: Feature gating mechanism
- `input/`, `input_impl/`: Type system for node I/O

**comfy_execution/** - Execution engine
- `caching.py`: Three-tier cache (BasicCache, HierarchicalCache, LRUCache) for avoiding redundant calculations
- `graph_utils.py`: Graph validation, linking, and execution order
- `validation.py`: Node input type checking
- `progress.py`: Progress tracking and isolation per execution

**comfy_extras/** - Built-in node implementations
- 70+ node files (samplers, model loading, image processing, audio, video)
- Each file defines nodes for specific functionality (e.g., `nodes_controlnet.py`, `nodes_flux.py`)

**comfy_api_nodes/** - Public node API definitions
- `apis/`: Define public-facing node interfaces
- `util/`: Helper functions for node development
- Separate from implementation, allows version control of node contracts

**api_server/** - HTTP API routes
- `routes/`: REST endpoints for execution, node info, etc.
- Follows standard REST patterns with WebSocket for real-time updates

**app/** - Application management
- `frontend_management.py`: Frontend versioning and serving
- `custom_node_manager.py`: Custom node discovery and lifecycle
- `model_manager.py`: Model file management
- `user_manager.py`: User authentication and management
- `subgraph_manager.py`: Nested workflow/subgraph management
- `logger.py`: Structured logging configuration (prefer this over print statements)
- `app_settings.py`: Application configuration
- `database/`: SQLAlchemy models and migrations (alembic_db/)

### Execution Flow

1. **Node Registration**: Nodes are registered via `@node_registry` or `@latest.node()` in Python
2. **Graph Building**: Frontend sends JSON workflow → `Graph` validates → prepares execution
3. **Execution Context**: Each execution isolated with `ExecutingContext` for safety (see `comfy_execution/utils.py`)
4. **Execution**: `Executor` processes nodes in order, managing GPU memory and caching
5. **Caching Strategy**: Uses input signature or node ID via `caching.py` to avoid redundant execution
6. **Progress Tracking**: Per-execution progress state with WebSocket updates (isolated per `ExecutingContext`)
7. **Async-First**: Entire system is async/await; all I/O operations are non-blocking

### Node System

Nodes are Python classes with:
- `INPUT_TYPES`: Dict defining input parameters and types
- `RETURN_TYPES`: Tuple of output type names
- `FUNCTION`: Method name to execute
- Class method that implements the logic

Example pattern:
```python
class MyNode:
    INPUT_TYPES = {
        "required": {
            "input": ("IMAGE",),
        }
    }
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "execute"

    def execute(self, input):
        # Process input
        return (output,)
```

## Common Development Commands

### Running ComfyUI
```bash
# Basic execution (requires GPU or --cpu flag)
python main.py

# With custom model paths
python main.py --extra-model-paths-config extra_model_paths.yaml

# Development with hot-reload (some parameters)
python main.py --listen 0.0.0.0 --port 8188

# CPU-only mode (very slow, for testing)
python main.py --cpu

# Enable high-quality TAESD previews
python main.py --preview-method taesd

# Enable verbose logging for debugging
python main.py --verbose

# Check available model paths
python main.py --list-model-paths
```

### Setting Up Development

```bash
# Install core dependencies
pip install -r requirements.txt

# Install unit test dependencies
pip install -r tests-unit/requirements.txt

# Install integration test dependencies (for inference tests)
pip install pytest websocket-client==1.6.1 opencv-python==4.6.0.66 scikit-image==0.21.0

# For linting (ruff is configured in pyproject.toml)
pip install ruff
```

### Running Tests

```bash
# Unit tests (fast, no GPU needed)
pytest tests-unit/

# Run specific test file
pytest tests-unit/comfy_test/folder_path_test.py

# Run specific test
pytest tests-unit/comfy_test/folder_path_test.py::test_specific_test

# Integration tests (slower, may need GPU)
pytest tests/execution/

# Inference quality tests (requires models)
pytest tests/inference/

# Generate baseline for quality regression
pytest tests/inference --output_dir tests/inference/baseline

# Run with coverage
pytest tests-unit/ --cov=. --cov-report=term-only
```

### Code Quality

```bash
# Linting (ruff is the primary linter)
ruff check . --select E,F,W

# Format code (ruff can auto-fix many issues)
ruff check . --fix

# Check for print statements (T rule - development should use logging)
ruff check . --select T

# pylint for additional checks
pylint <file_or_module>
```

## Testing Strategy

### Unit Tests (tests-unit/)
- Fast, no external dependencies
- Test individual functions and modules
- Located in `tests-unit/` mirroring source structure
- Use pytest fixtures for common setup

### Integration/Execution Tests (tests/execution/)
- Test node execution and graph evaluation
- Use `testing-pack/` custom nodes for test scenarios
- Test async execution, caching, progress isolation
- Slower but validate real behavior

### Inference Tests (tests/inference/)
- Quality regression testing
- Compares generated images against baseline
- Requires GPU and models
- Use with `--output_dir` to generate new baselines

### Test Patterns
- Use `conftest.py` for shared fixtures
- Mock GPU operations with CPU fallback in unit tests
- Isolate progress state per execution context
- Validate node input/output types

## Code Organization Standards

### File Naming
- Core modules: `snake_case.py` (e.g., `model_management.py`)
- Node files: `nodes_<feature>.py` (e.g., `nodes_controlnet.py`)
- Test files: `test_<module>.py` or `<module>_test.py`

### Package Organization
- **By domain**: Model loading, sampling, nodes, API routes
- **No mixed concerns**: Keep model code separate from API code
- **Version compatibility**: Legacy APIs in versioned directories
- **Execution isolation**: Each execution has its own context via `ExecutingContext`

### Import Patterns
- Relative imports within packages: `from .utils import helper`
- Absolute imports from root: `import comfy.model_management`
- Node imports: `import nodes` (central node registry)
- Logging imports: `from app.logger import setup_logger` (use structured logging, not print statements)

### Async Patterns
- All HTTP handlers are `async def` (uses `aiohttp`)
- Node execution functions can be sync or async
- Use `await` when calling async functions
- WebSocket communication is event-driven; subscribe to events from `server.py`

## Database and Migrations

### Alembic Setup
```bash
# Create new migration after changing models in app/database/models.py
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# View migration history
alembic history
```

### Database Models
Located in `app/database/models.py` using SQLAlchemy ORM. Migrations use Alembic. Database choice can vary (SQLite default, but supports others).

## Custom Node Development

### Basic Node Structure
```python
from comfy_api.latest import io

@io.node(
    title="My Custom Node",
    category="image/processing",
    description="Does something to images"
)
class MyCustomNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "strength": ("FLOAT", {"default": 1.0, "min": 0, "max": 2.0})
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("result",)
    FUNCTION = "execute"

    def execute(self, image, strength):
        # Implementation here
        return (result,)

NODE_CLASS_MAPPINGS = {"MyCustomNode": MyCustomNode}
NODE_DISPLAY_NAMES = {"MyCustomNode": "My Custom Node"}
```

### Node Categories
Common categories: `image/processing`, `image/generation`, `loaders`, `conditioning`, `model_merge`, `video`, `audio`, `sampling`, `advanced`

### Type System
Basic types: `IMAGE`, `CONDITIONING`, `MODEL`, `CLIP`, `VAE`, `LATENT`, `FLOAT`, `INT`, `STRING`
Custom types can be defined as tuples of allowed values.

## API and Frontend

### API Architecture
- **WebSocket**: Real-time updates (queue status, progress, results)
- **REST**: File uploads, model info, node schemas
- **Binary Protocol**: Optimized image transfer via WebSocket

### Frontend Communication
Frontend is in separate repository: [ComfyUI_frontend](https://github.com/Comfy-Org/ComfyUI_frontend)
- Weekly updates merged into core
- Use `--front-end-version` flag to use specific versions

### Key API Endpoints
- `/api/nodes`: Get node schema and info
- `/api/prompt`: Submit workflow execution
- `/api/history`: Get execution results
- `/api/interrupt`: Cancel execution
- `/api/queue`: Get/manage execution queue

## Performance Considerations

### Memory Management
- `model_management.py` handles GPU memory with smart offloading
- Models are unloaded when not in use to maximize VRAM efficiency
- Supports low-VRAM mode with `--normalvram`, `--lowvram`, `--cpu-vram`

### Execution Optimization
- Only parts of graph with changes execute (smart caching)
- Input signature caching prevents redundant node execution
- Async queue allows multiple submissions while processing

### Model Loading
- Models cached in memory once loaded
- Checkpoint format validation prevents corruption
- Custom model paths support via `extra_model_paths.yaml`

## Debugging

### Enable Verbose Logging
```bash
python main.py --verbose
```

### Check Model Paths
```bash
python main.py --list-model-paths
```

### Common Issues

1. **Torch CUDA not available**: Uninstall torch and reinstall with correct index
   ```bash
   pip uninstall torch && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
   ```

2. **Out of VRAM**: Use lower VRAM mode
   ```bash
   python main.py --lowvram  # Unload between operations
   python main.py --cpu-vram # Use CPU for non-GPU operations
   ```

3. **Missing models**: Check `models/` directory structure and `extra_model_paths.yaml`

## Git Workflow

**Default Branch**: `master`

### Branch Naming
- Features: `feature/description`
- Fixes: `fix/description`
- Never commit directly to `master`

### Pull Request Process
- Reference issue numbers: `Fixes #123`
- Include test coverage
- Pass all CI checks (unit tests, ruff linting)

## Release Process

ComfyUI follows a **weekly release cycle** (typically Friday):
1. **ComfyUI Core** releases stable version
2. **Desktop** builds using latest stable core
3. **Frontend** weekly updates frozen for release, development continues next cycle

Three interconnected repos:
- [ComfyUI Core](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI Desktop](https://github.com/Comfy-Org/desktop)
- [ComfyUI Frontend](https://github.com/Comfy-Org/ComfyUI_frontend)

## Documentation Resources

- **Official Docs**: https://docs.comfy.org/
- **Examples**: https://comfyanonymous.github.io/ComfyUI_examples/
- **Discord**: https://comfy.org/discord
- **Matrix**: https://app.element.io/#/room/%23comfyui_space%3Amatrix.org
- **Contributing Guide**: See `CONTRIBUTING.md`

## Key Files to Know

| File | Purpose |
|------|---------|
| `main.py` | Entry point, initializes paths and custom nodes; loads CLI args and setup |
| `server.py` | aiohttp web server, WebSocket handling, event system |
| `execution.py` | Core execution engine at root level (distinction from `comfy_execution/`) |
| `nodes.py` | Central node registry (99KB of built-in nodes) |
| `folder_paths.py` | Directory management for models and outputs |
| `comfy_execution/graph.py` | Graph structure and validation |
| `comfy_execution/caching.py` | Three-tier caching system |
| `comfy_execution/progress.py` | Progress tracking with execution isolation |
| `comfy_execution/utils.py` | Execution context management (`ExecutingContext`) |
| `app/database/models.py` | SQLAlchemy ORM definitions |
| `app/logger.py` | Structured logging setup |
| `comfy/model_management.py` | GPU/memory management and model loading |
| `comfy/cli_args.py` | CLI argument parsing and default configurations |
| `comfy_api/latest/__init__.py` | Public API decorators (`@node()`) |
| `comfy_api/feature_flags.py` | Feature gating for experimental features |
| `comfy_extras/nodes_*.py` | Built-in node implementations |
| `middleware/cache_middleware.py` | HTTP cache control middleware |

## Python Version Compatibility

- **Minimum**: Python 3.9
- **Recommended**: Python 3.13
- **3.14**: Works with kornia dependency commented out (breaks canny node)
- **Custom node issues**: Try Python 3.12 if 3.13 dependencies fail

## Linting and Code Standards

**Tool**: Ruff (configured in `pyproject.toml`)

Enabled rules:
- `E`: PEP 8 errors
- `F`: Pyflakes (undefined names, syntax errors)
- `W`: PEP 8 warnings
- `N805`: Invalid method argument names
- `S307`: Eval usage warning
- `S102`: Exec usage warning
- `T`: Print statement detection (use logging instead)

Disabled rules in pylint: Over 30+ rules disabled for flexibility (line length, docstrings, etc.)

## Contributing Notes

- Check [Discord](https://comfy.org/discord) #help or #feedback for questions
- See [contributing guide](https://github.com/comfyanonymous/ComfyUI/wiki/How-to-Contribute-Code) for PR process
- Search existing issues before creating new ones
- Use reactions (+1/-1) instead of "+1" comments on issues

## Important Development Patterns

### Execution Isolation
Each execution must use `ExecutingContext` to prevent cross-execution state pollution. Access via:
```python
from comfy_execution.utils import get_executing_context
context = get_executing_context()
```

### Logging Instead of Print
Use structured logging from `app.logger` instead of print statements:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Message with context", extra={"key": "value"})
```

### Type Validation
Node inputs are validated via `comfy_execution/validation.py`. Define INPUT_TYPES carefully:
```python
INPUT_TYPES = {
    "required": {
        "param": ("TYPE_NAME",),  # Tuple with type name
        "number": ("INT", {"default": 0, "min": 0, "max": 100})
    },
    "optional": {
        "extra": ("STRING", {"default": ""})
    }
}
```

### Nested Workflows
Use `SubgraphManager` (in `app/subgraph_manager.py`) for workflow composition and reuse. Allows workflows to contain other workflows as nodes.

### Feature Flags
Check `comfy_api/feature_flags.py` before implementing experimental features. Use flags to gate functionality during development:
```python
from comfy_api import feature_flags
if feature_flags.get_flag("experimental_feature"):
    # New behavior
```

### WebSocket Events
Subscribe to WebSocket events from `server.py` for real-time updates. Common events:
- `execution_start`: Workflow execution began
- `execution_progress`: Step progress update
- `execution_error`: Execution failed
- `execution_cached`: Results loaded from cache
