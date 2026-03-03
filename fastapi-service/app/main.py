import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from contract_parser import parse_openapi
from test_executor import run_test_suite
from schema_validator import validate_response
from diff_engine import compare_runs
from report_generator import generate_html_report

app = FastAPI(
    title="QA Service",
    description="Central FastAPI service for N8N QA pipelines",
    version="1.0.0"
)

BASELINES_DIR = os.getenv("BASELINES_DIR", "/data/baselines")
REPORTS_DIR = os.getenv("REPORTS_DIR", "/data/reports")


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("VALIDATION ERROR:", exc.errors())
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=422, content={"detail": str(exc.errors())})


# ── Pipeline 1: Contract Ingestion ────────────────────────────────────────────

class ContractRequest(BaseModel):
    spec: Dict[str, Any]          # Full OpenAPI JSON object
    environment: str = "staging"

@app.post("/debug-contract")
async def debug_contract(request: Request):
    body = await request.json()
    return {
        "spec_type": type(body.get("spec")).__name__,
        "spec_keys": list(body.get("spec", {}).keys()) if isinstance(body.get("spec"), dict) else "NOT A DICT",
        "top_level_keys": list(body.keys())
    }

@app.post("/parse-contract")
def parse_contract(req: ContractRequest):
    try:
        test_cases = parse_openapi(req.spec)
        return {
            "environment": req.environment,
            "test_case_count": len(test_cases),
            "test_cases": [tc.model_dump() for tc in test_cases]
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


# ── Pipeline 2: Test Executor ─────────────────────────────────────────────────

class TestRequest(BaseModel):
    test_cases: List[Dict[str, Any]]
    fuzz: bool = False
    sla_thresholds: Optional[Dict[str, int]] = None

@app.post("/run-tests")
async def run_tests(req: TestRequest):
    try:
        results = await run_test_suite(
            req.test_cases,
            fuzz=req.fuzz,
            sla_thresholds=req.sla_thresholds
        )
        passed = sum(1 for r in results if r["passed"])
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "pass_rate": round(passed / len(results) * 100, 1) if results else 0,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Pipeline 3: Regression & Diff ────────────────────────────────────────────

class DiffRequest(BaseModel):
    baseline: Dict[str, Any]
    current: Dict[str, Any]

@app.post("/compare-runs")
def compare(req: DiffRequest):
    try:
        report = compare_runs(req.baseline, req.current)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Pipeline 4: Report Generation ────────────────────────────────────────────

class ReportRequest(BaseModel):
    run_summary: Dict[str, Any]
    save_to_disk: bool = True

@app.post("/generate-report")
def generate_report(req: ReportRequest):
    try:
        html = generate_html_report(req.run_summary)
        path = None
        if req.save_to_disk:
            import os, datetime
            ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
            path = f"{REPORTS_DIR}/qa_report_{ts}.html"
            os.makedirs(REPORTS_DIR, exist_ok=True)
            with open(path, "w") as f:
                f.write(html)
        return {"html": html, "saved_to": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))