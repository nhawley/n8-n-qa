import jsonschema
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ValidationResult:
  passed: bool
  violations: List[str]
  severity: str  # 'critical', 'major', 'minor'

def validate_response(body: dict, schema: dict) -> ValidationResult:
  validator = jsonschema.Draft7Validator(schema)
  errors = sorted(validator.iter_errors(body),
                  key=jsonschema.exceptions.relevance)
  violations = [
      f'{list(e.path)}: {e.message}' for e in errors
  ]
  severity = 'minor'
  if any('required' in v for v in violations): severity = 'critical'
  if any('type' in v for v in violations): severity = 'major'
  return ValidationResult(
      passed=len(violations) == 0,
      violations=violations,
      severity=severity
  )