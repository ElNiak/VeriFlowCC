# API Specification

This is the API specification for the spec detailed in @.agilevv/specs/2025-08-14-fake-project-integration/spec.md

> Created: 2025-08-14
> Version: 1.0.0

## Factory API Extensions

### FakeProjectFactory Class

**Purpose:** Extend AgileVVDirFactory with project template capabilities
**Integration:** Seamless extension of existing factory pattern

```python
class FakeProjectFactory:
    def create_web_app_project(
        self,
        name: str,
        tech_stack: str = "python-fastapi",
        complexity: str = "simple",
        business_domain: str = "ecommerce"
    ) -> PathConfig
```

**Purpose:** Generate realistic web application projects
**Parameters:**

- name: Project identifier
- tech_stack: Technology stack (python-fastapi, typescript-react, etc.)
- complexity: Project complexity level (simple, medium, complex)
- business_domain: Business domain for realistic content
  **Response:** PathConfig with generated project structure
  **Errors:** ValidationError for invalid parameters

### Template Management API

```python
def list_available_templates(self) -> list[ProjectTemplate]
```

**Purpose:** List all available project templates
**Parameters:** None
**Response:** List of ProjectTemplate objects with metadata
**Errors:** None

```python
def create_from_template(
    self,
    template_id: str,
    name: str,
    customizations: dict[str, Any] = None
) -> PathConfig
```

**Purpose:** Create project from specific template with customizations
**Parameters:**

- template_id: Unique template identifier
- name: Project name
- customizations: Template variable overrides
  **Response:** PathConfig with generated project
  **Errors:** TemplateNotFoundError, ValidationError

## Testing Framework API

### Scenario Builder

```python
def create_test_scenario(
    self,
    scenario_name: str,
    projects: list[ProjectConfig],
    validation_rules: list[ValidationRule]
) -> TestScenario
```

**Purpose:** Create complex multi-project test scenarios
**Parameters:**

- scenario_name: Unique scenario identifier
- projects: List of project configurations to generate
- validation_rules: Rules for validating VeriFlowCC behavior
  **Response:** TestScenario object ready for execution
  **Errors:** ConfigurationError for invalid scenario setup

### Validation Framework

```python
def validate_verifflowcc_workflow(
    self,
    project: PathConfig,
    expected_stages: list[str],
    quality_thresholds: dict[str, float]
) -> WorkflowValidationResult
```

**Purpose:** Validate complete VeriFlowCC workflow execution on generated project
**Parameters:**

- project: Generated project to test
- expected_stages: V-Model stages that should complete successfully
- quality_thresholds: Quality gate thresholds for validation
  **Response:** WorkflowValidationResult with detailed metrics
  **Errors:** WorkflowError for execution failures
