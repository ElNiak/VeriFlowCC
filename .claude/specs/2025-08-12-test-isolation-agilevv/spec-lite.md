# Spec Summary (Lite)

Implement a configurable base directory system for .agilevv/ to enable complete test isolation through separate .agilevv-test/ directories. Tests will run in isolated temporary environments with configurable data sharing and cleanup strategies, while production maintains backward compatibility with the default .agilevv/ folder. This prevents test pollution, enables parallel test execution, and protects developer workflows.
