# VoiceHive Backend

AI voice agents for enterprise call handling.

## Quick Start

```bash
# Setup development environment
make setup-dev

# Run development server
make run-dev

# Run tests
make test

# View API documentation
open http://localhost:8000/docs
```

## Documentation

Complete documentation is available in the [`docs/`](./docs/) directory:

- [**README.md**](./docs/README.md) - Comprehensive project documentation
- [**API Documentation**](http://localhost:8000/docs) - Interactive Swagger UI
- [**ReDoc**](http://localhost:8000/redoc) - Alternative API documentation

## Development

```bash
# Install dependencies
make install

# Run tests with coverage
make test-cov

# Code quality checks
make lint

# Format code
make format

# Run with Docker
make run-docker
```

## Project Structure

```
voicehive-backend/
├── app/                    # Application code
├── tests/                  # Test suite
├── docs/                   # Documentation
├── Dockerfile             # Container configuration
├── Makefile              # Development commands
└── pyproject.toml        # Project configuration
```

## License

MIT License - see [docs/README.md](./docs/README.md) for details.
