# Scoring API

This project provides a declarative language for defining request structures and a validation system for ensuring that requests to a scoring HTTP API service adhere to the specified format. 
It is a part of Homework for the OTUS course and is intended for educational purposes.

## Features

- **Makefile**:
  - `make utest`: Runs unittest.
  - `make start`: Start the HTTP server with the supported API.
- **MIT License**: Open-source and free to use.

## Prerequisites

- Python 3.11 or higher.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/speculzzz/scoring_api.git
   cd scoring_api
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the local HTTP server  

```bash
make start
```

### Testing

Run the unittest:
```bash
make utest
```

## Project Structure

- `Makefile`: Automation for the local operations.
- `pyproject.toml`: Configuration for build tools and type checkers.
- `requirements.txt`: Project dependencies.
- `LICENSE`: MIT License.
- `README.md`: This file.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Author

- **speculzzz** (speculzzz@gmail.com)

---

Feel free to use it!