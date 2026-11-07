def test_tenant_scoping_is_required_in_queries():
    # Regression guard: every company-owned record endpoint must filter by authenticated company_id.
    assert 'company_id' in open('app/enterprise_routes.py',encoding='utf-8').read()
