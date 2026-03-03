import asyncio
import time
import httpx
from typing import List, Dict, Any, Optional

DEFAULT_SLA = {'GET': 500, 'POST': 800, 'PUT': 800, 'DELETE': 600}

async def run_test_suite(
    test_cases: List[Dict[str, Any]],
    fuzz: bool = False,
    sla_thresholds: Optional[Dict[str, int]] = None
) -> List[Dict[str, Any]]:
    sla = sla_thresholds or DEFAULT_SLA
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [_run_single(client, case, sla) for case in test_cases]
        return await asyncio.gather(*tasks)

async def _run_single(
    client: httpx.AsyncClient,
    case: Dict[str, Any],
    sla: Dict[str, int]
) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        r = await client.request(
            method=case['method'],
            url=case['endpoint'],
            params=case.get('params', {})
        )
        latency = (time.perf_counter() - t0) * 1000
        sla_limit = sla.get(case['method'], 1000)
        passed = (
            r.status_code in case.get('expected_status', [200]) and
            latency < sla_limit
        )
        return {
            "endpoint": case['endpoint'],
            "method": case['method'],
            "status_code": r.status_code,
            "latency_ms": round(latency, 2),
            "performance_pass": latency < sla_limit,
            "passed": passed,
            "error": None
        }
    except Exception as e:
        return {
            "endpoint": case['endpoint'],
            "method": case['method'],
            "status_code": None,
            "latency_ms": None,
            "performance_pass": False,
            "passed": False,
            "error": str(e)
        }