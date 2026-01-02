import pandas as pd

from core.report_generator import ComprehensiveReportBuilder, ReportMetadata


def test_builder_generates_json_and_html(tmp_path):
    metadata = ReportMetadata(title="Test Report", author="Tester", description="Desc")
    builder = ComprehensiveReportBuilder(metadata)
    builder.add_executive_summary("Summary text")

    df = pd.DataFrame({"Metric": ["A", "B"], "Value": [1, 2]})
    builder.add_scenario_comparison(df)

    json_path = tmp_path / "report.json"
    html_path = tmp_path / "report.html"

    out_json = builder.generate_json(str(json_path))
    out_html = builder.generate_html(str(html_path))

    assert json_path.exists()
    assert html_path.exists()
    assert out_json == str(json_path)
    assert out_html == str(html_path)

    # Ensure HTML contains section title and table header
    html_text = html_path.read_text(encoding="utf-8")
    assert "Scenario Comparison" in html_text
    assert "Metric" in html_text
