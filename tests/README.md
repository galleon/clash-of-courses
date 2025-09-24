# BRS Prototype Test Suite

This directory contains a comprehensive test suite for the Business Requirements Specification (BRS) prototype, using `uv` for dependency management and Python test execution.

## Setup

The test environment is managed with `uv` and includes all necessary dependencies:

```bash
cd tests/
uv run --no-project python <test_name>.py
```

## Test Files

### 1. `test_comprehensive_thinking.py` ⭐ **[RECOMMENDED]**

**Purpose**: Comprehensive validation of the AI thinking model capabilities with multi-step reasoning and function calling.

**Features**:
- Tests qwen2.5:7b-instruct thinking model performance
- Validates 5-step decision framework (Student Profile, Course Requirements, Academic Progression, Risk Assessment, Final Recommendation)
- Tests batch review functionality
- Validates function chaining workflows
- Creates test data for realistic scenarios
- Comprehensive analysis of AI reasoning patterns

**Usage**:
```bash
uv run --no-project python test_comprehensive_thinking.py
```

**Best For**: Validating AI model improvements, testing thinking capabilities, function calling validation

---

### 2. `test_ui_workflow.py` ⭐ **[RECOMMENDED]**

**Purpose**: End-to-end test that recreates actual user interactions from the UI, providing real-world workflow validation.

**Features**:
- Simulates complete student-advisor workflow
- Tests request creation through chat interface
- Validates advisor review and approval process
- Checks database state consistency
- Provides detailed step-by-step output
- Based on actual user interactions

**Usage**:
```bash
uv run --no-project python test_ui_workflow.py
```

**Best For**: Integration testing, workflow validation, regression testing

---

### 3. `test_workflow_clean.py`

**Purpose**: Clean, focused test of the core advisor approval workflow without complex database reset operations.

**Features**:
- Tests complete approval workflow
- Student request → Advisor review → Approval decision
- Clean, readable test structure
- Good for debugging specific workflow issues
- No database manipulation overhead

**Usage**:
```bash
uv run --no-project python test_workflow_clean.py
```

**Best For**: Quick workflow validation, debugging approval logic

---

### 4. `test_approval_only.py`

**Purpose**: Focused test specifically for the approval functionality, ideal for testing approval logic in isolation.

**Features**:
- Minimal, focused scope
- Tests only the approval mechanism
- Quick execution
- Good for approval-specific debugging
- Simple pass/fail validation

**Usage**:
```bash
uv run --no-project python test_approval_only.py
```

**Best For**: Approval mechanism testing, quick validation of approval changes

## Testing Strategy

### For Development:
1. **Daily workflow testing**: Use `test_ui_workflow.py`
2. **AI model validation**: Use `test_comprehensive_thinking.py`
3. **Quick approval checks**: Use `test_approval_only.py`

### For CI/CD:
1. Run `test_comprehensive_thinking.py` for AI capabilities
2. Run `test_ui_workflow.py` for integration validation
3. Run `test_workflow_clean.py` for core workflow verification

### Prerequisites

Before running tests, ensure:
1. Docker containers are running: `docker-compose up -d`
2. Backend is healthy: `curl http://localhost:8000/health`
3. Database is seeded with test personas
4. Ollama model is available (qwen2.5:7b-instruct)

## Test Environment

- **Dependency Management**: `uv` with `pyproject.toml`
- **Python Version**: >=3.11
- **Required Services**: Backend (8000), Database (5432), Ollama (11434)
- **Test Data**: Uses seeded personas (Sarah Ahmed, Dr. Ahmad Mahmoud, etc.)

## Expected Output

All tests provide detailed console output with:
- ✅ Success indicators
- ❌ Failure messages
- 📊 Status information
- 🧠 AI analysis results
- 📝 Response previews

## Troubleshooting

**Common Issues**:
1. **Connection errors**: Ensure `docker-compose up -d` is running
2. **User not found**: Database may need reseeding
3. **AI model errors**: Check Ollama service and model availability
4. **422 errors**: Request validation issues, check payload format

**Debug Steps**:
1. Check service health: `curl http://localhost:8000/health`
2. Verify users exist: `curl http://localhost:8000/users/`
3. Check requests: `curl http://localhost:8000/requests/`
4. Review container logs: `docker-compose logs backend`
