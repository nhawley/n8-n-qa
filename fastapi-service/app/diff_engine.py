from deepdiff import DeepDiff
from enum import Enum
from typing import Dict, Any

class RegressionSeverity(str, Enum):
    BREAKING = 'breaking'
    DEGRADED = 'degraded'
    WARNING  = 'warning'
    CLEAN    = 'clean'

def classify_diff(diff: DeepDiff) -> RegressionSeverity:
    if diff.get('dictionary_item_removed'): return RegressionSeverity.BREAKING
    if diff.get('type_changes'):            return RegressionSeverity.BREAKING
    if diff.get('iterable_item_removed'):   return RegressionSeverity.DEGRADED
    if diff.get('dictionary_item_added'):   return RegressionSeverity.WARNING
    if not diff:                            return RegressionSeverity.CLEAN
    return RegressionSeverity.WARNING

def compare_runs(baseline: Dict[str, Any], current: Dict[str, Any]) -> dict:
    regressions = []
    for endpoint in current:
        if endpoint not in baseline:
            continue
        diff = DeepDiff(
            baseline[endpoint].get('schema_sample', {}),
            current[endpoint].get('schema_sample', {}),
            ignore_order=True
        )
        severity = classify_diff(diff)
        if severity != RegressionSeverity.CLEAN:
            regressions.append({
                'endpoint': endpoint,
                'severity': severity.value,
                'diff': str(diff),
                'latency_delta': (
                    current[endpoint].get('avg_latency', 0) -
                    baseline[endpoint].get('avg_latency', 0)
                )
            })
    return {
        'regressions': regressions,
        'total': len(regressions),
        'has_breaking': any(r['severity'] == 'breaking' for r in regressions)
    }