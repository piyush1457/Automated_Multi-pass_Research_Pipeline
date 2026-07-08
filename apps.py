"""
apps.py — canonical list of 100 apps across 10 categories (10 per category).
Derived exactly from the assignment brief.
"""

APPS = [
    # ── 1. CRM and Sales ──────────────────────────────────────────────
    {"id": 1,   "name": "Salesforce",                "category": "CRM and Sales",                "slug": "salesforce"},
    {"id": 2,   "name": "HubSpot",                   "category": "CRM and Sales",                "slug": "hubspot"},
    {"id": 3,   "name": "Pipedrive",                 "category": "CRM and Sales",                "slug": "pipedrive"},
    {"id": 4,   "name": "Attio",                     "category": "CRM and Sales",                "slug": "attio"},
    {"id": 5,   "name": "Twenty",                    "category": "CRM and Sales",                "slug": "twenty"},
    {"id": 6,   "name": "Podio",                     "category": "CRM and Sales",                "slug": "podio"},
    {"id": 7,   "name": "Zoho CRM",                  "category": "CRM and Sales",                "slug": "zohocrm"},
    {"id": 8,   "name": "Close",                     "category": "CRM and Sales",                "slug": "close"},
    {"id": 9,   "name": "Copper",                    "category": "CRM and Sales",                "slug": "copper"},
    {"id": 10,  "name": "DealCloud",                 "category": "CRM and Sales",                "slug": "dealcloud"},

    # ── 2. Support and Helpdesk ───────────────────────────────────────
    {"id": 11,  "name": "Zendesk",                   "category": "Support and Helpdesk",          "slug": "zendesk"},
    {"id": 12,  "name": "Intercom",                  "category": "Support and Helpdesk",          "slug": "intercom"},
    {"id": 13,  "name": "Freshdesk",                 "category": "Support and Helpdesk",          "slug": "freshdesk"},
    {"id": 14,  "name": "Front",                     "category": "Support and Helpdesk",          "slug": "front"},
    {"id": 15,  "name": "Pylon",                     "category": "Support and Helpdesk",          "slug": "pylon"},
    {"id": 16,  "name": "LiveAgent",                 "category": "Support and Helpdesk",          "slug": "liveagent"},
    {"id": 17,  "name": "Plain",                     "category": "Support and Helpdesk",          "slug": "plain"},
    {"id": 18,  "name": "Help Scout",                "category": "Support and Helpdesk",          "slug": "helpscout"},
    {"id": 19,  "name": "Gorgias",                   "category": "Support and Helpdesk",          "slug": "gorgias"},
    {"id": 20,  "name": "Gladly",                    "category": "Support and Helpdesk",          "slug": "gladly"},

    # ── 3. Communications and Messaging ───────────────────────────────
    {"id": 21,  "name": "Slack",                     "category": "Communications and Messaging",  "slug": "slack"},
    {"id": 22,  "name": "Twilio",                    "category": "Communications and Messaging",  "slug": "twilio"},
    {"id": 23,  "name": "Zoho Cliq",                 "category": "Communications and Messaging",  "slug": "zoho_cliq"},
    {"id": 24,  "name": "Lark (Larksuite)",          "category": "Communications and Messaging",  "slug": "lark"},
    {"id": 25,  "name": "Pumble",                    "category": "Communications and Messaging",  "slug": "pumble"},
    {"id": 26,  "name": "Discord",                   "category": "Communications and Messaging",  "slug": "discord"},
    {"id": 27,  "name": "Telegram",                  "category": "Communications and Messaging",  "slug": "telegram"},
    {"id": 28,  "name": "WhatsApp Business",          "category": "Communications and Messaging",  "slug": "whatsapp"},
    {"id": 29,  "name": "Aircall",                   "category": "Communications and Messaging",  "slug": "aircall"},
    {"id": 30,  "name": "Vonage",                    "category": "Communications and Messaging",  "slug": "vonage"},

    # ── 4. Marketing, Ads, Email and Social ───────────────────────────
    {"id": 31,  "name": "Google Ads",                "category": "Marketing, Ads, Email and Social", "slug": "google_ads"},
    {"id": 32,  "name": "Meta Ads",                  "category": "Marketing, Ads, Email and Social", "slug": "meta_ads"},
    {"id": 33,  "name": "LinkedIn Ads",              "category": "Marketing, Ads, Email and Social", "slug": "linkedin_ads"},
    {"id": 34,  "name": "GoHighLevel",               "category": "Marketing, Ads, Email and Social", "slug": "gohighlevel"},
    {"id": 35,  "name": "Mailchimp",                 "category": "Marketing, Ads, Email and Social", "slug": "mailchimp"},
    {"id": 36,  "name": "Klaviyo",                   "category": "Marketing, Ads, Email and Social", "slug": "klaviyo"},
    {"id": 37,  "name": "systeme.io",                "category": "Marketing, Ads, Email and Social", "slug": "systemeio"},
    {"id": 38,  "name": "Pinterest",                 "category": "Marketing, Ads, Email and Social", "slug": "pinterest"},
    {"id": 39,  "name": "Threads (Meta)",            "category": "Marketing, Ads, Email and Social", "slug": "threads"},
    {"id": 40,  "name": "SendGrid",                  "category": "Marketing, Ads, Email and Social", "slug": "sendgrid"},

    # ── 5. Ecommerce ──────────────────────────────────────────────────
    {"id": 41,  "name": "Shopify",                   "category": "Ecommerce",                    "slug": "shopify"},
    {"id": 42,  "name": "WooCommerce",               "category": "Ecommerce",                    "slug": "woocommerce"},
    {"id": 43,  "name": "BigCommerce",               "category": "Ecommerce",                    "slug": "bigcommerce"},
    {"id": 44,  "name": "Salesforce Commerce Cloud", "category": "Ecommerce",                    "slug": "salesforce_commerce_cloud"},
    {"id": 45,  "name": "Magento (Adobe Commerce)",  "category": "Ecommerce",                    "slug": "magento"},
    {"id": 46,  "name": "Squarespace",               "category": "Ecommerce",                    "slug": "squarespace"},
    {"id": 47,  "name": "Ecwid",                     "category": "Ecommerce",                    "slug": "ecwid"},
    {"id": 48,  "name": "Gumroad",                   "category": "Ecommerce",                    "slug": "gumroad"},
    {"id": 49,  "name": "Amazon Selling Partner",    "category": "Ecommerce",                    "slug": "amazon"},
    {"id": 50,  "name": "fanbasis",                  "category": "Ecommerce",                    "slug": "fanbasis"},

    # ── 6. Data, SEO and Scraping ─────────────────────────────────────
    {"id": 51,  "name": "DataForSEO",                "category": "Data, SEO and Scraping",       "slug": "dataforseo"},
    {"id": 52,  "name": "SE Ranking",                "category": "Data, SEO and Scraping",       "slug": "seranking"},
    {"id": 53,  "name": "Ahrefs",                    "category": "Data, SEO and Scraping",       "slug": "ahrefs"},
    {"id": 54,  "name": "MrScraper",                 "category": "Data, SEO and Scraping",       "slug": "mrscraper"},
    {"id": 55,  "name": "Apify",                     "category": "Data, SEO and Scraping",       "slug": "apify"},
    {"id": 56,  "name": "Firecrawl",                 "category": "Data, SEO and Scraping",       "slug": "firecrawl"},
    {"id": 57,  "name": "Bright Data",               "category": "Data, SEO and Scraping",       "slug": "brightdata"},
    {"id": 58,  "name": "Sherlock",                  "category": "Data, SEO and Scraping",       "slug": "sherlock"},
    {"id": 59,  "name": "Waterfall.io",              "category": "Data, SEO and Scraping",       "slug": "waterfall"},
    {"id": 60,  "name": "Clay",                      "category": "Data, SEO and Scraping",       "slug": "clay"},

    # ── 7. Developer, Infra and Data platforms ────────────────────────
    {"id": 61,  "name": "GitHub",                    "category": "Developer, Infra and Data platforms", "slug": "github"},
    {"id": 62,  "name": "Vercel",                    "category": "Developer, Infra and Data platforms", "slug": "vercel"},
    {"id": 63,  "name": "Netlify",                   "category": "Developer, Infra and Data platforms", "slug": "netlify"},
    {"id": 64,  "name": "Cloudflare",                "category": "Developer, Infra and Data platforms", "slug": "cloudflare"},
    {"id": 65,  "name": "Supabase",                  "category": "Developer, Infra and Data platforms", "slug": "supabase"},
    {"id": 66,  "name": "Neo4j",                     "category": "Developer, Infra and Data platforms", "slug": "neo4j"},
    {"id": 67,  "name": "Snowflake",                 "category": "Developer, Infra and Data platforms", "slug": "snowflake"},
    {"id": 68,  "name": "MongoDB Atlas",             "category": "Developer, Infra and Data platforms", "slug": "mongodb"},
    {"id": 69,  "name": "Datadog",                   "category": "Developer, Infra and Data platforms", "slug": "datadog"},
    {"id": 70,  "name": "Sentry",                    "category": "Developer, Infra and Data platforms", "slug": "sentry"},

    # ── 8. Productivity and Project Management ────────────────────────
    {"id": 71,  "name": "Notion",                    "category": "Productivity and Project Management", "slug": "notion"},
    {"id": 72,  "name": "Airtable",                  "category": "Productivity and Project Management", "slug": "airtable"},
    {"id": 73,  "name": "Linear",                    "category": "Productivity and Project Management", "slug": "linear"},
    {"id": 74,  "name": "Jira",                      "category": "Productivity and Project Management", "slug": "jira"},
    {"id": 75,  "name": "Asana",                     "category": "Productivity and Project Management", "slug": "asana"},
    {"id": 76,  "name": "Monday.com",                "category": "Productivity and Project Management", "slug": "monday"},
    {"id": 77,  "name": "ClickUp",                   "category": "Productivity and Project Management", "slug": "clickup"},
    {"id": 78,  "name": "Coda",                      "category": "Productivity and Project Management", "slug": "coda"},
    {"id": 79,  "name": "Smartsheet",                "category": "Productivity and Project Management", "slug": "smartsheet"},
    {"id": 80,  "name": "Harvest",                   "category": "Productivity and Project Management", "slug": "harvest"},

    # ── 9. Finance and Fintech ────────────────────────────────────────
    {"id": 81,  "name": "Stripe",                    "category": "Finance and Fintech",          "slug": "stripe"},
    {"id": 82,  "name": "Plaid",                     "category": "Finance and Fintech",          "slug": "plaid"},
    {"id": 83,  "name": "Binance",                   "category": "Finance and Fintech",          "slug": "binance"},
    {"id": 84,  "name": "Paygent Connect",           "category": "Finance and Fintech",          "slug": "paygent"},
    {"id": 85,  "name": "iPayX",                     "category": "Finance and Fintech",          "slug": "ipayx"},
    {"id": 86,  "name": "QuickBooks",                "category": "Finance and Fintech",          "slug": "quickbooks"},
    {"id": 87,  "name": "Xero",                      "category": "Finance and Fintech",          "slug": "xero"},
    {"id": 88,  "name": "Brex",                      "category": "Finance and Fintech",          "slug": "brex"},
    {"id": 89,  "name": "Ramp",                      "category": "Finance and Fintech",          "slug": "ramp"},
    {"id": 90,  "name": "PitchBook",                 "category": "Finance and Fintech",          "slug": "pitchbook"},

    # ── 10. AI, Research and Media-native ─────────────────────────────
    {"id": 91,  "name": "NotebookLM",                "category": "AI, Research and Media-native", "slug": "notebooklm"},
    {"id": 92,  "name": "Otter AI",                  "category": "AI, Research and Media-native", "slug": "otter"},
    {"id": 93,  "name": "Fathom",                    "category": "AI, Research and Media-native", "slug": "fathom"},
    {"id": 94,  "name": "Consensus",                 "category": "AI, Research and Media-native", "slug": "consensus"},
    {"id": 95,  "name": "Reducto",                   "category": "AI, Research and Media-native", "slug": "reducto"},
    {"id": 96,  "name": "Devin",                     "category": "AI, Research and Media-native", "slug": "devin"},
    {"id": 97,  "name": "higgsfield",                "category": "AI, Research and Media-native", "slug": "higgsfield"},
    {"id": 98,  "name": "Mermaid CLI",               "category": "AI, Research and Media-native", "slug": "mermaid"},
    {"id": 99,  "name": "YouTube Transcript",        "category": "AI, Research and Media-native", "slug": "youtubetranscript"},
    {"id": 100, "name": "Grain",                     "category": "AI, Research and Media-native", "slug": "grain"},
]

CATEGORIES = [
    "CRM and Sales",
    "Support and Helpdesk",
    "Communications and Messaging",
    "Marketing, Ads, Email and Social",
    "Ecommerce",
    "Data, SEO and Scraping",
    "Developer, Infra and Data platforms",
    "Productivity and Project Management",
    "Finance and Fintech",
    "AI, Research and Media-native",
]

# Quick lookups
APP_BY_ID   = {a["id"]: a for a in APPS}
APP_BY_SLUG = {a["slug"]: a for a in APPS}
APP_BY_NAME = {a["name"]: a for a in APPS}
