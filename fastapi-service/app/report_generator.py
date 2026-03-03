def generate_html_report(run_summary: dict) -> str:
    passed = run_summary.get('passed', 0)
    failed = run_summary.get('failed', 0)
    total = passed + failed
    pass_rate = round(passed / total * 100, 1) if total else 0
    color = '#22c55e' if pass_rate == 100 else '#ef4444'

    rows = ''
    for r in run_summary.get('results', []):
        status = '✅' if r.get('passed') else '❌'
        rows += f'''<tr>
            <td>{r.get("method","")}</td>
            <td>{r.get("endpoint","")}</td>
            <td>{r.get("status_code","")}</td>
            <td>{r.get("latency_ms","")}ms</td>
            <td>{status}</td>
        </tr>'''

    return f'''<!DOCTYPE html>
    <html><head><title>QA Report</title>
    <style>
      body {{ font-family: Arial; padding: 2rem; }}
      .metric {{ font-size: 2rem; font-weight: bold; color: {color} }}
      table {{ border-collapse: collapse; width: 100%; }}
      th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
      th {{ background: #1E3A5F; color: white; }}
    </style>
    </head><body>
    <h1>API QA Report — {run_summary.get("timestamp","")}</h1>
    <div class="metric">{pass_rate}% Pass Rate ({passed}/{total})</div>
    <table>
      <tr><th>Method</th><th>Endpoint</th><th>Status</th><th>Latency</th><th>Pass</th></tr>
      {rows}
    </table>
    </body></html>'''