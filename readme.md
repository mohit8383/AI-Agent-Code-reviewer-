# 🤖 AI Code Review Agent

A powerful command-line interface for automated code analysis and review using AI. This tool helps developers identify security vulnerabilities, performance issues, style problems, and code quality concerns across multiple programming languages.

## ✨ Features

* **Multi-language Support**: Python, JavaScript, TypeScript, Java, C++, C#, PHP, Ruby, Go, Rust
* **Comprehensive Analysis**: Security, performance, style, complexity, and documentation checks
* **Rich CLI Interface**: Beautiful terminal output with progress bars and colored results
* **Flexible Configuration**: YAML/JSON configuration files with customizable rules
* **Multiple Output Formats**: Detailed terminal output, JSON export, HTML reports
* **Batch Processing**: Analyze entire directories or specific files
* **Code Improvement**: Download improved versions of your code
* **Server Integration**: Works with Flask backend for distributed analysis

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-code-review-agent.git
cd ai-code-review-agent

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .[dev]
```

### Basic Usage

1. **Start the Flask server** (in one terminal):

```bash
python app.py
```

2. **Create a configuration file**:

```bash
python cli.py create-config
```

3. **Analyze your code**:

```bash
# Analyze current directory
python cli.py analyze .

# Analyze specific files
python cli.py analyze src/main.py src/utils.py

# Use custom configuration
python cli.py analyze . --config custom_config.yaml
```

## 📖 Detailed Usage

### Command Reference

#### Create Configuration

```bash
python cli.py create-config
```

Creates a sample `code_review_config.yaml` file with default settings.

#### Analyze Code

```bash
python cli.py analyze <paths> [options]
```

**Options:**

* `--config, -c`: Configuration file path (default: code\_review\_config.yaml)
* `--server, -s`: Server URL (default: [http://localhost:5000](http://localhost:5000))
* `--format, -f`: Output format (detailed|json)
* `--extensions`: File extensions to include
* `--output, -o`: Save results to file
* `--report`: HTML report output file
* `--no-report`: Skip HTML report generation
* `--download-improved`: Download improved code package

### Configuration Examples

#### Basic Configuration

```yaml
# code_review_config.yaml
analysis:
  security: true
  performance: true
  style: true
  complexity: true

rules:
  styleGuide: "pep8"
  maxLineLength: 120
  maxComplexity: 10

output:
  format: "detailed"
  includeFixSuggestions: true
  generateReport: true

filters:
  minSeverity: "low"
  excludeFiles:
    - ".git/*"
    - "node_modules/*"
    - "*.min.js"
```

#### Advanced Configuration

```yaml
analysis:
  security: true
  performance: true
  style: true
  complexity: true
  documentation: true
  testing: true

rules:
  styleGuide: "google"
  maxLineLength: 100
  maxComplexity: 8
  maxFunctionLength: 50
  allowUnsafeOperations: false
  checkSQLInjection: true
  checkXSS: true

output:
  format: "detailed"
  includeFixSuggestions: true
  generateReport: true
  showLineNumbers: true
  includeCodeContext: true

filters:
  minSeverity: "medium"
  excludeFiles:
    - "tests/*"
    - "*.min.js"
    - "__pycache__/*"
  includeExtensions:
    - ".py"
    - ".js"
    - ".ts"
  maxFileSize: 5

advanced:
  maxWorkers: 4
  enableCache: true
  aiModel: "gpt-4"
```

## 💡 Usage Examples

### Example 1: Quick Analysis

```bash
# Analyze current directory with default settings
python cli.py analyze .
```

### Example 2: Custom Configuration

```bash
# Create custom config
python cli.py create-config

# Edit the generated config file, then analyze
python cli.py analyze src/ --config code_review_config.yaml
```

### Example 3: Specific File Types

```bash
# Only analyze Python and JavaScript files
python cli.py analyze . --extensions .py .js
```

### Example 4: JSON Output

```bash
# Output results as JSON for further processing
python cli.py analyze . --format json --output results.json
```

### Example 5: Skip HTML Report

```bash
# Analyze without generating HTML report
python cli.py analyze . --no-report
```

### Example 6: Download Improvements

```bash
# Analyze and download improved code
python cli.py analyze . --download-improved improved_code.zip
```

### Example 7: Multiple Directories

```bash
# Analyze multiple directories
python cli.py analyze src/ tests/ utils/
```

## 🔧 Development Setup

### Prerequisites

* Python 3.8+
* Flask 2.3+
* Rich (for CLI formatting)
* PyYAML
* Requests
* Click

### Installation for Development

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-code-review-agent.git
cd ai-code-review-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_cli.py

# Run with verbose output
pytest -v
```

### Code Quality Checks

```bash
# Format code with black
black src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

## 📊 Output Examples

### Terminal Output

```
🔍 AI Code Review Agent
📁 Analyzing: ./src

Progress: ██████████ 100% | 15/15 files

📋 Analysis Results:
🏐 File: src/main.py
🔴 HIGH: Potential SQL injection vulnerability (line 42)
🟡 MEDIUM: Function too complex (line 15)
🟢 LOW: Missing docstring (line 8)

📈 Summary:
• Files analyzed: 15
• Issues found: 23
• High severity: 2
• Medium severity: 8
• Low severity: 13

💡 Suggestions:
• Consider refactoring complex functions
• Add input validation for user data
• Improve documentation coverage
```

### JSON Output

```json
{
  "summary": {
    "filesAnalyzed": 15,
    "totalIssues": 23,
    "highSeverity": 2,
    "mediumSeverity": 8,
    "lowSeverity": 13,
    "analysisTime": "2.3s"
  },
  "files": [
    {
      "path": "src/main.py",
      "language": "python",
      "issues": [
        {
          "type": "security",
          "severity": "high",
          "line": 42,
          "column": 15,
          "message": "Potential SQL injection vulnerability",
          "rule": "sql-injection-check",
          "suggestion": "Use parameterized queries",
          "codeContext": "cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")"
        }
      ]
    }
  ]
}
```

## 🛠️ API Reference

### Server Endpoints

#### POST /analyze

Analyze code files or directories.

**Request Body:**

```json
{
  "files": [
    {
      "path": "main.py",
      "content": "def hello():\n    print('Hello, World!')",
      "language": "python"
    }
  ],
  "config": {
    "analysis": {
      "security": true,
      "performance": true,
      "style": true
    }
  }
}
```

**Response:**

```json
{
  "status": "success",
  "results": {
    "summary": {...},
    "files": [...]
  }
}
```

#### GET /health

Check server health status.

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "3600s"
}
```

## 🎯 Supported Languages

| Language   | Extension | Style Guide  | Security Checks |
| ---------- | --------- | ------------ | --------------- |
| Python     | .py       | PEP8, Google | ✅               |
| JavaScript | .js       | StandardJS   | ✅               |
| TypeScript | .ts       | TSLint       | ✅               |
| Java       | .java     | Google, Sun  | ✅               |
| C++        | .cpp, .cc | Google       | ✅               |
| C#         | .cs       | Microsoft    | ✅               |
| PHP        | .php      | PSR-12       | ✅               |
| Ruby       | .rb       | RuboCop      | ✅               |
| Go         | .go       | gofmt        | ✅               |
| Rust       | .rs       | rustfmt      | ✅               |

## 🔒 Security Analysis

The tool checks for common security vulnerabilities:

* **SQL Injection**: Detects unsafe database queries
* **XSS**: Cross-site scripting vulnerabilities
* **CSRF**: Cross-site request forgery issues
* **Path Traversal**: Directory traversal attacks
* **Command Injection**: OS command injection
* **Hardcoded Secrets**: API keys, passwords in code
* **Insecure Crypto**: Weak encryption methods
* **Authentication**: Missing or weak auth checks

## 📈 Performance Analysis

Performance checks include:

* **Complexity**: Cyclomatic complexity analysis
* **Memory Usage**: Potential memory leaks
* **Loop Efficiency**: Nested loops and optimization
* **Database Queries**: N+1 query problems
* **Caching**: Missing cache opportunities
* **Async/Await**: Blocking operations
* **Algorithm Efficiency**: Big O analysis

## 🎨 Style Analysis

Style checks cover:

* **Naming Conventions**: Variables, functions, classes
* **Code Formatting**: Indentation, spacing, line length
* **Documentation**: Docstrings, comments
* **Code Organization**: Import order, structure
* **Language-Specific**: Following language conventions

## 🔧 Configuration Reference

### Analysis Options

```yaml
analysis:
  security: true          # Enable security checks
  performance: true       # Enable performance analysis
  style: true            # Enable style checks
  complexity: true       # Enable complexity analysis
  documentation: true    # Check documentation
  testing: true         # Analyze test coverage
```

### Rule Configuration

```yaml
rules:
  styleGuide: "pep8"           # Style guide to follow
  maxLineLength: 120           # Maximum line length
  maxComplexity: 10           # Maximum cyclomatic complexity
  maxFunctionLength: 50       # Maximum function length
  allowUnsafeOperations: false # Allow unsafe operations
  checkSQLInjection: true     # Check for SQL injection
  checkXSS: true             # Check for XSS vulnerabilities
  requireDocstrings: true    # Require function docstrings
```

### Output Configuration

```yaml
output:
  format: "detailed"          # Output format (detailed|json|brief)
  includeFixSuggestions: true # Include fix suggestions
  generateReport: true        # Generate HTML report
  showLineNumbers: true       # Show line numbers in output
  includeCodeContext: true    # Include code context
  colorOutput: true          # Use colored output
```

### Filter Configuration

```yaml
filters:
  minSeverity: "low"         # Minimum severity level
  excludeFiles:              # Files to exclude
    - ".git/*"
    - "node_modules/*"
    - "*.min.js"
  includeExtensions:         # File extensions to include
    - ".py"
    - ".js"
    - ".ts"
  maxFileSize: 5            # Maximum file size in MB
```

## 🚀 Performance Tips

1. **Use File Filters**: Exclude unnecessary files to speed up analysis
2. **Limit File Size**: Set `maxFileSize` to avoid analyzing large files
3. **Parallel Processing**: Increase `maxWorkers` for faster analysis
4. **Enable Caching**: Set `enableCache: true` for repeated analyses
5. **Selective Analysis**: Disable unnecessary analysis types

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Standards

* Follow PEP 8 for Python code
* Add type hints for all functions
* Write comprehensive tests
* Update documentation for new features
* Use meaningful commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔚 Support

* **Documentation**: Check this README and inline help (`python cli.py --help`)
* **Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/ai-code-review-agent/issues)
* **Discussions**: Join conversations on [GitHub Discussions](https://github.com/mohit8383/-code-review-agent)
* **Email**: Contact us at [support@yourcompany.com](mailto:mohitkasat83@gmail.com)

## 🎉 Acknowledgments

* Thanks to all contributors who have helped improve this tool
* Inspired by popular static analysis tools like ESLint, Pylint, and SonarQube
* Built with amazing open-source libraries

---

**Happy Coding! 🚀**
