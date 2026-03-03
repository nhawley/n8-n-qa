import yaml
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class TestCase(BaseModel):
    endpoint: str
    method: str
    params: Dict[str, Any] = {}
    expected_status: List[int]
    response_schema: Optional[Dict] = None
    tags: List[str] = []
    security: List[str] = []

def parse_openapi(spec: dict) -> List[TestCase]:
    test_cases = []
    base_url = spec.get('servers', [{}])[0].get('url', '')
    for path, methods in spec.get('paths', {}).items():
        for method, op in methods.items():
            if method not in ('get', 'post', 'put', 'delete', 'patch'):
                continue
            statuses = [int(s) for s in op.get('responses', {}).keys() if s.isdigit()]
            schema = _extract_response_schema(op)
            params = _extract_example_params(op)

            security_raw = op.get('security', [])
            if isinstance(security_raw, dict):
                security = list(security_raw.keys())
            elif isinstance(security_raw, list):
                security = [k for scheme in security_raw for k in scheme.keys()]
            else:
                security = []

            test_cases.append(TestCase(
                endpoint=f'{base_url}{path}',
                method=method.upper(),
                params=params,
                expected_status=statuses or [200],
                response_schema=schema,
                tags=op.get('tags', []),
                security=security
            ))
    return test_cases

def _extract_response_schema(op: dict) -> Optional[dict]:
    try:
        return (op.get('responses', {})
                  .get('200', {})
                  .get('content', {})
                  .get('application/json', {})
                  .get('schema'))
    except Exception:
        return None

def _extract_example_params(op: dict) -> dict:
    params = {}
    for p in op.get('parameters', []):
        if p.get('example'):
            params[p['name']] = p['example']
        elif p.get('schema', {}).get('example'):
            params[p['name']] = p['schema']['example']
    return params