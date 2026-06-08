"""Default MVP UAT checklist items (ASCII-only)."""

DEFAULT_CHECKLIST_ITEMS = [
    {
        "section": "Login and dashboard",
        "title": "Login with demo account",
        "description": "Authenticate with admin@example.com",
        "expected_result": "User lands on dashboard with tenant context",
    },
    {
        "section": "Login and dashboard",
        "title": "Dashboard executive overview",
        "description": "Review stats, quick actions, security summary",
        "expected_result": "KPI cards and recent activity load without errors",
    },
    {
        "section": "Agent gallery",
        "title": "Browse 10 agent templates",
        "description": "Open /agents/ and verify categories",
        "expected_result": "All templates show Brain Active badge",
    },
    {
        "section": "Agent playground",
        "title": "Sales agent playground scenario",
        "description": "Load pricing scenario and send message",
        "expected_result": "Structured reply with intent returned",
    },
    {
        "section": "Sales agent flow",
        "title": "CRM lead auto-update",
        "description": "After playground, check CRM leads",
        "expected_result": "Lead created or updated with score/status",
    },
    {
        "section": "Other 9 agents smoke",
        "title": "Open second agent playground",
        "description": "Test clinic or real estate agent",
        "expected_result": "Agent responds without error",
    },
    {
        "section": "Web chat",
        "title": "Web chat demo message",
        "description": "Send message via /inbox/webchat/",
        "expected_result": "Conversation and AI reply appear in inbox",
    },
    {
        "section": "WhatsApp mock",
        "title": "WhatsApp mock test",
        "description": "Run integration test message",
        "expected_result": "Webhook event processed successfully",
    },
    {
        "section": "Instagram mock",
        "title": "Instagram mock channel visible",
        "description": "Verify channel in integrations",
        "expected_result": "Instagram mock channel listed and active",
    },
    {
        "section": "Inbox",
        "title": "Unified inbox thread",
        "description": "Open conversation detail",
        "expected_result": "Messages display with sender types",
    },
    {
        "section": "CRM leads/pipeline",
        "title": "CRM leads list and pipeline",
        "description": "Review leads and kanban board",
        "expected_result": "Demo leads visible with correct statuses",
    },
    {
        "section": "Knowledge base",
        "title": "Knowledge sources searchable",
        "description": "View knowledge list and content",
        "expected_result": "Sources exist for demo agents",
    },
    {
        "section": "Analytics",
        "title": "Analytics dashboard KPIs",
        "description": "Open /analytics/ with date range",
        "expected_result": "Overview metrics and agent runs display",
    },
    {
        "section": "Settings/team/roles",
        "title": "Settings and team pages",
        "description": "Owner views workspace and team settings",
        "expected_result": "Settings load; role restrictions work for rep",
    },
    {
        "section": "Plan/usage",
        "title": "Plan and usage limits",
        "description": "Review plan card and usage bars",
        "expected_result": "Enterprise plan and usage metrics shown",
    },
    {
        "section": "Security dashboard",
        "title": "Security status review",
        "description": "Open /settings/security/",
        "expected_result": "Encryption, rate limit, and blocker cards visible",
    },
    {
        "section": "Demo report",
        "title": "Printable demo report",
        "description": "Open /demo/report/ and print preview",
        "expected_result": "Report shows 60/60 QA and module list",
    },
]
