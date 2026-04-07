"""Tests for list_templates tool."""

import json


class TestListTemplates:
    def test_list_all(self):
        from cx_task_harness.tools.templates import list_templates
        result = list_templates()
        assert "templates" in result
        assert len(result["templates"]) >= 1

    def test_filter_by_industry(self):
        from cx_task_harness.tools.templates import list_templates
        result = list_templates(industry="ecommerce")
        for t in result["templates"]:
            assert t["industry"] == "ecommerce"

    def test_filter_by_locale(self):
        from cx_task_harness.tools.templates import list_templates
        result = list_templates(locale="ko")
        for t in result["templates"]:
            assert t["locale"] == "ko"

    def test_filter_by_industry_and_locale(self):
        from cx_task_harness.tools.templates import list_templates
        result = list_templates(industry="ecommerce", locale="en")
        for t in result["templates"]:
            assert t["industry"] == "ecommerce"
            assert t["locale"] == "en"

    def test_template_summary_fields(self):
        from cx_task_harness.tools.templates import list_templates
        result = list_templates(locale="en")
        if result["templates"]:
            t = result["templates"][0]
            assert "id" in t
            assert "name" in t
            assert "description" in t
            assert "industry" in t
            assert "steps_count" in t
            assert "step_types" in t

    def test_get_template(self):
        from cx_task_harness.tools.templates import get_template
        spec_json = get_template("ecommerce/order_cancel", "en")
        assert spec_json is not None
        data = json.loads(spec_json)
        assert data["id"] == "ecommerce-order-cancel"

    def test_get_template_not_found(self):
        from cx_task_harness.tools.templates import get_template
        result = get_template("nonexistent/template", "en")
        assert result is None

    def test_all_templates_are_valid_task_specs(self):
        from cx_task_harness.tools.templates import list_templates, get_template
        from cx_task_harness.tools.validator import validate_task_spec

        for locale in ["en", "ko"]:
            result = list_templates(locale=locale)
            for t in result["templates"]:
                spec_json = get_template(t["id"], t["locale"])
                assert spec_json is not None
                v = validate_task_spec(spec_json)
                assert v["valid"], f"Template {t['id']} ({t['locale']}) invalid: {v['errors']}"
