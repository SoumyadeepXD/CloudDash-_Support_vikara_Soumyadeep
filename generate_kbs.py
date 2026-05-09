import json
import os

os.makedirs("/Users/soumyadeepxd/Developer/clouddash-support/knowledge_base/articles", exist_ok=True)

kbs = [
    {
        "id": "KB-001", "title": "How to reset your CloudDash API key", "category": "FAQs", "tags": ["api", "security", "keys"],
        "content": "To reset your CloudDash API key, log in to your account and navigate to Settings > API Keys. Click on the 'Revoke & Generate New Key' button next to your active key. Make sure to update your application with the new key immediately, as the old key will stop working instantly. This process ensures your CloudDash account remains secure. If you have automated pipelines, remember to rotate the keys in your secrets manager. For Enterprise customers, key rotation can be enforced every 90 days.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-002", "title": "What cloud providers does CloudDash support", "category": "FAQs", "tags": ["providers", "aws", "gcp", "azure"],
        "content": "CloudDash natively supports Amazon Web Services (AWS), Google Cloud Platform (GCP), and Microsoft Azure. For AWS, we integrate via CloudWatch and CloudTrail. For GCP, we use Google Cloud Operations suite (formerly Stackdriver). For Azure, we pull metrics directly from Azure Monitor. Setting up a new provider takes less than 5 minutes using our 1-click IAM role provisioner. Each provider dashboard gives you a unified view of your instances, databases, and network usage. Multi-cloud cost comparison is available on the Pro and Enterprise tiers.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-003", "title": "How to invite team members and manage roles", "category": "FAQs", "tags": ["team", "rbac", "users"],
        "content": "You can invite new team members from the Team Settings page. Click 'Invite Member', enter their email address, and select a role (Viewer, Editor, Admin, or Billing Manager). Viewers can only see dashboards; Editors can create and modify alerts; Admins have full access including user management; Billing Managers only see cost data and invoices. You can change a user's role at any time. If you use SSO (Enterprise plan only), role mapping can be configured directly in your identity provider.",
        "applies_to": ["Pro", "Enterprise"]
    },
    {
        "id": "KB-004", "title": "CloudDash pricing plans comparison", "category": "FAQs", "tags": ["pricing", "plans", "billing"],
        "content": "CloudDash offers three main plans. Starter ($49/mo) includes basic monitoring for up to 50 cloud resources, 7-day data retention, and email support. Pro ($199/mo) includes up to 500 resources, 30-day retention, multi-cloud cost optimization, and priority support. Enterprise (Custom pricing starting at $999/mo) includes unlimited resources, 1-year data retention, SSO/SAML integrations, dedicated account manager, and custom RBAC roles. Overages on Starter and Pro are billed at $1 per additional resource.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-005", "title": "Alerts not firing — step-by-step diagnosis", "category": "Troubleshooting", "tags": ["alerts", "notifications", "debug"],
        "content": "If your alerts are not firing, follow these steps. 1. Check the alert threshold configuration: Ensure the metric actually crossed the threshold for the required duration (e.g., CPU > 80% for 5 minutes). 2. Check the integration status: Go to Integrations > Webhooks/Slack/Email and verify the endpoints are active and returning 200 OK. 3. Check the alert history logs: Navigate to Logs > Alerts to see if the alert was suppressed due to a maintenance window or rate limiting. 4. Verify your cloud provider's metrics are flowing into CloudDash (check the Data Sources page). If metrics are stale, re-authenticate your IAM role.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-006", "title": "Dashboard loading slowly — performance troubleshooting", "category": "Troubleshooting", "tags": ["performance", "dashboard", "slow"],
        "content": "A slow-loading dashboard is typically caused by querying too much historical data or having too many widgets on a single view. To improve performance: 1. Reduce the time window from 30 days to 7 days or 24 hours. 2. Use aggregated metrics (e.g., daily averages) instead of raw data points for long timeframes. 3. Break down large dashboards into smaller, focused ones (e.g., separate 'Database Metrics' from 'Frontend Metrics'). 4. Clear your browser cache or try incognito mode. If the issue persists across all users, check the CloudDash Status page for any ongoing platform incidents.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-007", "title": "AWS CloudWatch integration failing", "category": "Troubleshooting", "tags": ["aws", "cloudwatch", "integration"],
        "content": "If your AWS CloudWatch integration fails, it is usually an IAM permission issue. Ensure the IAM Role assigned to CloudDash has the 'CloudWatchReadOnlyAccess' policy attached. The role must also have a Trust Relationship allowing 'arn:aws:iam::123456789012:role/CloudDashCrossAccountRole' to assume it. Error 403 AccessDenied means the role is incorrect. Error 429 TooManyRequests means you are hitting AWS API limits; CloudDash will automatically retry with exponential backoff, but you may need to request a quota increase from AWS if you have thousands of resources.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-008", "title": "GCP Monitoring integration setup and troubleshooting", "category": "Troubleshooting", "tags": ["gcp", "monitoring", "setup"],
        "content": "To set up GCP Monitoring, you need to create a Service Account in your GCP project with the 'Monitoring Viewer' and 'Compute Viewer' roles. Generate a JSON key for this service account and upload it to CloudDash. If metrics are not appearing: 1. Ensure the Google Cloud Monitoring API is enabled in your GCP project. 2. Verify the JSON key is valid and not expired. 3. Check if the GCP project ID matches exactly. Common error 'PermissionDenied' means the service account lacks the required viewer roles.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-009", "title": "SSO setup with Okta/Azure AD", "category": "Troubleshooting", "tags": ["sso", "okta", "azure"],
        "content": "Single Sign-On (SSO) is available on the Enterprise plan. To configure Okta or Azure AD: 1. Go to Settings > Security > SSO Setup. 2. Copy the ACS URL and Entity ID provided by CloudDash. 3. In your Identity Provider (IdP), create a new SAML 2.0 application and paste these URLs. 4. Map the email attribute to 'nameID'. 5. Download the IdP metadata XML and upload it back to CloudDash. 6. Click 'Test Connection'. If it fails with 'Invalid Signature', ensure the x.509 certificate matches. Note: Just-In-Time (JIT) provisioning is enabled by default.",
        "applies_to": ["Enterprise"]
    },
    {
        "id": "KB-010", "title": "How to upgrade or downgrade your plan", "category": "Billing & Pricing", "tags": ["billing", "upgrade", "downgrade"],
        "content": "To change your subscription plan, navigate to Billing > Subscriptions. Click 'Change Plan' and select your new tier. Upgrades take effect immediately, and you will be charged a prorated amount for the remainder of the billing cycle. Downgrades take effect at the end of your current billing cycle to ensure you don't lose access to features you've already paid for. If you are downgrading from Pro to Starter, please ensure you have fewer than 50 resources and have exported any data older than 7 days, as it will be permanently deleted upon downgrade.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-011", "title": "Invoice explanation — what each line item means", "category": "Billing & Pricing", "tags": ["invoice", "billing", "charges"],
        "content": "Your monthly invoice contains several line items. 'Base Subscription' covers the flat fee for your chosen plan (Starter, Pro, or Enterprise). 'Resource Overages' applies if you monitored more resources than your plan's limit (billed at $1 per extra resource). 'SMS Alert Credits' are charges for SMS notifications beyond the free tier (100 included on Pro, $0.05 per SMS thereafter). 'Data Retention Add-on' appears if you purchased extended log storage. All invoices are finalized on the 1st of the month and charged to your default payment method.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-012", "title": "Refund and cancellation policy", "category": "Billing & Pricing", "tags": ["refund", "cancellation", "policy"],
        "content": "You can cancel your CloudDash subscription at any time from the Billing page. We offer a full refund if you cancel within 14 days of your initial purchase or an annual renewal. We do not provide partial month refunds for mid-cycle cancellations. If you experience an unexpected spike in overage charges due to a misconfiguration, please contact support within 7 days of the invoice date to request a one-time courtesy waiver. Refund disputes exceeding $500 are handled by our billing escalation team and may take up to 3 business days to resolve.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-013", "title": "Payment methods accepted and how to update", "category": "Billing & Pricing", "tags": ["payment", "credit card", "billing"],
        "content": "CloudDash accepts all major credit cards (Visa, Mastercard, American Express, Discover) via our secure Stripe integration. We also accept PayPal for all plans. For Enterprise customers billed annually, we support manual invoicing via wire transfer or ACH. To update your payment method, go to Billing > Payment Methods, click 'Add New Card', and set it as the default. We recommend keeping a backup payment method on file to prevent service interruptions if your primary card expires or declines.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-014", "title": "CloudDash REST API — authentication and rate limits", "category": "API Documentation", "tags": ["api", "rest", "limits"],
        "content": "The CloudDash REST API is available at `https://api.clouddash.com/v1/`. Authenticate by passing your API key in the `Authorization: Bearer <token>` header. Rate limits depend on your plan: Starter allows 100 requests/minute, Pro allows 1,000 requests/minute, and Enterprise allows 10,000 requests/minute. If you exceed the limit, the API returns a 429 Too Many Requests response with a `Retry-After` header. We strongly recommend implementing exponential backoff in your API clients to handle rate limits gracefully.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-015", "title": "Webhook configuration — events, payloads, retry logic", "category": "API Documentation", "tags": ["webhooks", "api", "events"],
        "content": "Webhooks allow you to receive real-time HTTP POST requests when specific events occur in CloudDash, such as `alert.triggered` or `cost.anomaly_detected`. The payload is in JSON format and includes the event ID, timestamp, and resource details. If your endpoint returns a non-2xx status code, CloudDash will retry delivering the webhook up to 5 times over 24 hours (with exponential backoff). You can verify the payload authenticity using the `X-CloudDash-Signature` header, which is an HMAC-SHA256 hash of the request body signed with your webhook secret.",
        "applies_to": ["Pro", "Enterprise"]
    },
    {
        "id": "KB-016", "title": "SDK quickstart guide", "category": "API Documentation", "tags": ["sdk", "python", "node"],
        "content": "CloudDash provides official SDKs for Python and Node.js. To install the Python SDK, run `pip install clouddash-sdk`. To install the Node.js SDK, run `npm install clouddash-node`. Both SDKs automatically handle authentication, pagination, and rate limit retries. Example Python usage: `import clouddash; client = clouddash.Client(api_key='YOUR_KEY'); alerts = client.alerts.list(status='active')`. Detailed SDK documentation and advanced examples for metric ingestion and custom dashboard creation are available on our GitHub repository.",
        "applies_to": ["Pro", "Enterprise"]
    },
    {
        "id": "KB-017", "title": "RBAC — roles and permissions matrix", "category": "Account & Access", "tags": ["rbac", "roles", "permissions"],
        "content": "Role-Based Access Control (RBAC) ensures your team members have the appropriate level of access. The 'Viewer' role can only view dashboards and alerts. The 'Editor' role can create, edit, and delete dashboards and alert rules. The 'Billing Manager' role can view invoices and change payment methods but cannot view cloud metrics. The 'Admin' role has full access, including managing users and API keys. Custom roles (e.g., 'Database Admin' restricted to RDS metrics only) can be configured exclusively on the Enterprise plan.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-018", "title": "Audit logs — how to access and interpret them", "category": "Account & Access", "tags": ["audit", "logs", "security"],
        "content": "Audit logs track all configuration changes, logins, and API usage within your CloudDash account for security and compliance purposes. To access audit logs, go to Settings > Security > Audit Logs (Pro and Enterprise plans only). Each log entry contains the timestamp, user email, IP address, action performed (e.g., `dashboard.deleted`, `user.invited`), and the resource ID affected. Logs are retained for 90 days on Pro and 1 year on Enterprise. You can also stream audit logs to an external S3 bucket via the Integrations page.",
        "applies_to": ["Pro", "Enterprise"]
    },
    {
        "id": "KB-019", "title": "Team and organization management", "category": "Account & Access", "tags": ["organization", "team", "workspaces"],
        "content": "In CloudDash, an 'Organization' represents your company, and 'Workspaces' represent different environments (e.g., Production, Staging) or departments. Users are invited to the Organization and then granted access to specific Workspaces. This allows you to segregate data and access control strictly. You can rename your Organization from the Settings page. If you need to transfer Organization ownership to another user, the current owner must initiate the transfer via the Security tab, and the new owner must accept it via email.",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    },
    {
        "id": "KB-020", "title": "CloudDash feature roadmap Q2-Q3 2026", "category": "General", "tags": ["roadmap", "features", "updates"],
        "content": "Our product roadmap for Q2-Q3 2026 includes several exciting updates. 1. AI-Powered Anomaly Detection: Automatically spot unusual traffic patterns without manual thresholds (Expected Q2). 2. Kubernetes Native Monitoring: Deep dive into pod and node health directly within the dashboard (Expected Q2). 3. Custom Metric Ingestion via OTLP: Native OpenTelemetry support for application metrics (Expected Q3). 4. Automated Cost Remediation: 1-click action to pause idle EC2 instances (Expected Q3). 5. Expanded SSO Providers: Adding native integrations for Ping Identity and OneLogin (Expected Q3).",
        "applies_to": ["Starter", "Pro", "Enterprise"]
    }
]

for kb in kbs:
    kb["last_updated"] = "2026-04-15"
    with open(f"/Users/soumyadeepxd/Developer/clouddash-support/knowledge_base/articles/{kb['id']}.json", "w") as f:
        json.dump(kb, f, indent=2)

print("Created 20 KB articles.")
