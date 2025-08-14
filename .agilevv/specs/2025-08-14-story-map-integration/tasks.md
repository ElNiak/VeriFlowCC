# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agilevv/specs/2025-08-14-story-map-integration/spec.md

> Created: 2025-08-14
> Status: Ready for Implementation

## Tasks

- [ ] 1. Create StoryMapManager Foundation

  - [ ] 1.1 Write tests for StoryMapManager class initialization and basic CRUD operations
  - [ ] 1.2 Create Pydantic schemas for Initiative, Epic, Feature, UserStory, and Task models
  - [ ] 1.3 Implement StoryMapManager class with JSON file persistence in `.agilevv/story_map.json`
  - [ ] 1.4 Add story map validation methods and error handling
  - [ ] 1.5 Format code, run linters and fix issues
  - [ ] 1.6 Verify all tests pass

- [ ] 2. Implement DoD Validation Framework

  - [ ] 2.1 Write tests for DoD validation at story, feature, and epic levels
  - [ ] 2.2 Create YAML-based DoD configuration system with default criteria
  - [ ] 2.3 Implement DoD validator class with configurable quality gates
  - [ ] 2.4 Add DoD validation results tracking and evidence collection
  - [ ] 2.5 Format code, run linters and fix issues
  - [ ] 2.6 Verify all tests pass

- [ ] 3. Create Story Map CLI Commands

  - [ ] 3.1 Write tests for story-map command group and subcommands
  - [ ] 3.2 Implement `story-map init` command with template support
  - [ ] 3.3 Implement `story-map add-epic` and `story-map add-story` commands
  - [ ] 3.4 Implement `story-map validate-dod` and `story-map status` commands
  - [ ] 3.5 Add CLI help text, error handling, and user feedback
  - [ ] 3.6 Format code, run linters and fix issues
  - [ ] 3.7 Verify all tests pass

- [ ] 4. Integrate with Existing Orchestrator

  - [ ] 4.1 Write tests for orchestrator integration and agent context enhancement
  - [ ] 4.2 Modify BaseAgent to include story map context in agent inputs
  - [ ] 4.3 Enhance orchestrator's `_prepare_comprehensive_agent_input` with story map data
  - [ ] 4.4 Integrate DoD validation into existing `_apply_advanced_gating` quality gates
  - [ ] 4.5 Update Sprint 0 and Sprint N workflows to include story map operations
  - [ ] 4.6 Format code, run linters and fix issues
  - [ ] 4.7 Verify all tests pass

- [ ] 5. Sprint 0 Story Map Integration

  - [ ] 5.1 Write tests for Sprint 0 story mapping workflow and user journey creation
  - [ ] 5.2 Enhance `init-sprint0` command to initialize story maps
  - [ ] 5.3 Create agent prompts for story map creation and user persona development
  - [ ] 5.4 Implement story map template system with default templates
  - [ ] 5.5 Add backward compatibility with existing backlog.md format
  - [ ] 5.6 Format code, run linters and fix issues
  - [ ] 5.7 Verify all tests pass
