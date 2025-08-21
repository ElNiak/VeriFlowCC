# Database Schema

This is the database schema implementation for the spec detailed in @.agilevv/specs/2025-08-21-quality-engineering-integration/spec.md

> Created: 2025-08-21
> Version: 1.0.0

## Database Changes

**New Tables:**

1. **quality_metrics** - Store quantitative quality measurements at each V-Model stage
1. **defect_tracking** - Systematic defect classification and root cause analysis data
1. **statistical_process_control** - Time-series data for SPC chart generation and trend analysis
1. **reliability_measurements** - Software reliability engineering model outputs and predictions
1. **test_effectiveness** - Systematic testing results and classification tree analysis data

**Schema Specifications:**

```sql
-- Quality Metrics Collection
CREATE TABLE quality_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    sprint_id TEXT NOT NULL,
    v_model_stage TEXT NOT NULL, -- requirements, design, coding, testing, integration
    metric_type TEXT NOT NULL, -- defect_density, complexity, coverage, reliability
    metric_value REAL NOT NULL,
    measurement_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    agent_type TEXT NOT NULL, -- requirements_analyst, architect, developer, qa_tester
    baseline_value REAL,
    threshold_upper REAL,
    threshold_lower REAL,
    statistical_significance REAL
);

-- Defect Tracking and Classification
CREATE TABLE defect_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    defect_id TEXT UNIQUE NOT NULL,
    discovery_stage TEXT NOT NULL, -- requirements, design, coding, testing, production
    defect_type TEXT NOT NULL, -- functional, performance, security, usability
    severity_level INTEGER NOT NULL, -- 1-5 scale
    root_cause_category TEXT, -- process, people, technology, environment
    prevention_strategy TEXT,
    resolution_time_hours REAL,
    detection_method TEXT, -- review, testing, static_analysis, user_report
    creation_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolution_timestamp DATETIME,
    cost_impact REAL
);

-- Statistical Process Control Data
CREATE TABLE statistical_process_control (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    process_name TEXT NOT NULL, -- code_review, testing, integration
    measurement_value REAL NOT NULL,
    measurement_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    control_limit_upper REAL NOT NULL,
    control_limit_lower REAL NOT NULL,
    warning_limit_upper REAL,
    warning_limit_lower REAL,
    out_of_control_flag BOOLEAN DEFAULT FALSE,
    trend_direction TEXT -- improving, stable, declining
);

-- Reliability Engineering Measurements
CREATE TABLE reliability_measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    sprint_id TEXT NOT NULL,
    failure_rate REAL,
    mean_time_to_failure REAL,
    reliability_prediction REAL,
    confidence_interval_lower REAL,
    confidence_interval_upper REAL,
    model_type TEXT NOT NULL, -- exponential, weibull, gamma
    measurement_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_points_count INTEGER,
    prediction_accuracy REAL
);

-- Test Effectiveness Analysis
CREATE TABLE test_effectiveness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    test_suite_id TEXT NOT NULL,
    classification_tree_path TEXT, -- hierarchical test classification
    test_case_count INTEGER,
    defects_found INTEGER,
    defects_prevented INTEGER,
    test_execution_time REAL,
    coverage_achieved REAL,
    effectiveness_score REAL, -- defects found per test hour
    systematic_testing_method TEXT, -- boundary, equivalence, combinatorial
    measurement_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX idx_quality_metrics_project_stage ON quality_metrics(project_id, v_model_stage);
CREATE INDEX idx_defect_tracking_project_type ON defect_tracking(project_id, defect_type);
CREATE INDEX idx_spc_process_timestamp ON statistical_process_control(process_name, measurement_timestamp);
CREATE INDEX idx_reliability_project_sprint ON reliability_measurements(project_id, sprint_id);
CREATE INDEX idx_test_effectiveness_project ON test_effectiveness(project_id, classification_tree_path);
```

## Rationale

**Quality Metrics Storage:** Enables Jeff Tian's quantitative quality improvement approach by maintaining historical quality data across V-Model stages with statistical significance tracking.

**Defect Classification System:** Implements systematic defect prevention strategies by categorizing defects according to Tian's classification methodologies and tracking prevention effectiveness.

**Statistical Process Control:** Provides foundation for Tian's SPC methodologies by storing time-series process data with control limits and trend analysis capabilities.

**Reliability Engineering Support:** Stores reliability model predictions and measurements to implement Tian's software reliability engineering approaches with confidence intervals.

**Test Effectiveness Measurement:** Captures systematic testing results using Tian's classification tree methods and effectiveness metrics for continuous testing improvement.

**Performance Considerations:** Indexed tables support rapid quality dashboard generation and statistical analysis queries without impacting V-Model execution performance.

**Data Integrity:** Normalized schema ensures consistent quality data collection across all agents while maintaining referential integrity for cross-stage analysis.
