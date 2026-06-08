"""Analytics business logic — aggregate metrics from existing tables."""
from apps.analytics import selectors
from apps.tenants.models import Tenant


class AnalyticsService:
    """Compute tenant-scoped analytics from CRM, inbox, agent engine, and knowledge."""

    @staticmethod
    def get_date_range(range_key: str):
        return selectors.get_date_range(range_key)

    @classmethod
    def get_overview_metrics(cls, tenant: Tenant, range_key: str = selectors.DEFAULT_RANGE) -> dict:
        range_key = range_key if range_key in selectors.VALID_RANGES else selectors.DEFAULT_RANGE
        data = selectors.get_overview_counts(tenant, range_key)
        data["range"] = range_key
        return data

    @classmethod
    def get_conversion_funnel(cls, tenant: Tenant, range_key: str = selectors.DEFAULT_RANGE) -> dict:
        range_key = range_key if range_key in selectors.VALID_RANGES else selectors.DEFAULT_RANGE
        counts = selectors.count_leads_by_status(tenant, range_key)
        total = sum(counts.values())
        stages = []
        for status in selectors.FUNNEL_STATUSES:
            count = counts.get(status.value, 0)
            percentage = round((count / total) * 100, 1) if total else 0
            stages.append({
                "status": status.value,
                "label": status.label,
                "count": count,
                "percentage": percentage,
            })
        return {"range": range_key, "total_leads": total, "stages": stages}

    @classmethod
    def get_lead_status_breakdown(cls, tenant: Tenant, range_key: str = selectors.DEFAULT_RANGE) -> dict:
        funnel = cls.get_conversion_funnel(tenant, range_key)
        return {
            "range": range_key,
            "total_leads": funnel["total_leads"],
            "breakdown": funnel["stages"],
        }

    @classmethod
    def get_lead_source_breakdown(cls, tenant: Tenant, range_key: str = selectors.DEFAULT_RANGE) -> dict:
        range_key = range_key if range_key in selectors.VALID_RANGES else selectors.DEFAULT_RANGE
        counts = selectors.count_leads_by_source(tenant, range_key)
        total = sum(counts.values())
        sources = []
        labels = {
            "web_chat": "Web Chat",
            "whatsapp": "WhatsApp",
            "instagram": "Instagram",
            "manual": "Manual",
            "other": "Other",
        }
        for bucket in selectors.SOURCE_BUCKETS:
            count = counts.get(bucket, 0)
            percentage = round((count / total) * 100, 1) if total else 0
            sources.append({
                "source": bucket,
                "label": labels[bucket],
                "count": count,
                "percentage": percentage,
            })
        return {"range": range_key, "total_leads": total, "sources": sources}

    @classmethod
    def get_agent_performance(cls, tenant: Tenant, range_key: str = selectors.DEFAULT_RANGE) -> dict:
        range_key = range_key if range_key in selectors.VALID_RANGES else selectors.DEFAULT_RANGE
        return {
            "range": range_key,
            "agents": selectors.get_agent_performance_rows(tenant, range_key),
        }

    @classmethod
    def get_inbox_metrics(cls, tenant: Tenant, range_key: str = selectors.DEFAULT_RANGE) -> dict:
        range_key = range_key if range_key in selectors.VALID_RANGES else selectors.DEFAULT_RANGE
        data = selectors.get_inbox_counts(tenant, range_key)
        data["range"] = range_key
        return data

    @classmethod
    def get_agent_engine_metrics(cls, tenant: Tenant, range_key: str = selectors.DEFAULT_RANGE) -> dict:
        range_key = range_key if range_key in selectors.VALID_RANGES else selectors.DEFAULT_RANGE
        data = selectors.get_agent_engine_counts(tenant, range_key)
        data["range"] = range_key
        return data

    @classmethod
    def get_knowledge_metrics(cls, tenant: Tenant, range_key: str = selectors.DEFAULT_RANGE) -> dict:
        range_key = range_key if range_key in selectors.VALID_RANGES else selectors.DEFAULT_RANGE
        data = selectors.get_knowledge_counts(tenant, range_key)
        data["range"] = range_key
        return data

    @classmethod
    def get_recent_activity(cls, tenant: Tenant, range_key: str = selectors.DEFAULT_RANGE) -> dict:
        range_key = range_key if range_key in selectors.VALID_RANGES else selectors.DEFAULT_RANGE
        data = selectors.get_recent_activity_rows(tenant, range_key)
        data["range"] = range_key
        return data

    @classmethod
    def get_full_dashboard(cls, tenant: Tenant, range_key: str = selectors.DEFAULT_RANGE) -> dict:
        range_key = range_key if range_key in selectors.VALID_RANGES else selectors.DEFAULT_RANGE
        return {
            "range": range_key,
            "overview": cls.get_overview_metrics(tenant, range_key),
            "funnel": cls.get_conversion_funnel(tenant, range_key),
            "lead_status": cls.get_lead_status_breakdown(tenant, range_key),
            "lead_sources": cls.get_lead_source_breakdown(tenant, range_key),
            "agents": cls.get_agent_performance(tenant, range_key),
            "inbox": cls.get_inbox_metrics(tenant, range_key),
            "agent_engine": cls.get_agent_engine_metrics(tenant, range_key),
            "knowledge": cls.get_knowledge_metrics(tenant, range_key),
            "recent_activity": cls.get_recent_activity(tenant, range_key),
        }
