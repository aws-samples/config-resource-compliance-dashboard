
The AI Governance module extends the AWS Config Resource Compliance Dashboard (CRCD) with three additional tabs that give security leads, compliance officers, and cloud architects a unified view of their AI governance posture on AWS. All data comes from AWS Config configuration snapshots — the same pipeline that powers the rest of CRCD. No additional infrastructure is required.

## Tabs

### AI Governance

![CRCD](../images/ai-governance.png "AWS Config Dashboard, AI Governance")

Executive overview of AI compliance posture, plus a detail tracker:

* **AI governance compliance rate** — gauge showing the percentage of AWS Config evaluations passing in the latest configuration snapshot. Traffic-light colors: green at or above 90%, amber at or above 70%, red below.
* **AI resources under governance / Resources with compliance gaps** — current counts of distinct AI resources tracked, and of resources with at least one failing evaluation.
* **Compliance by AI service** — stacked bar of compliant vs. non-compliant resources per AI service type.
* **Trend of COMPLIANT / NON_COMPLIANT AI resources** — month-over-month KPIs with sparkline, following the Compliance tab pattern.
* **Top failing AI Config rules** — the five rules with the most non-compliant resources.
* **Governance coverage (Sankey)** — flow diagram from AI service to AWS Config rule, weighted by evaluation volume. Shows at a glance which rules govern which services.
* **Compliance trend / Non-compliant trend by AI service** — weekly time series; a declining non-compliant area means governance gaps are being closed.
* **AI compliance tracker** — section mirroring the Compliance tab tracker: current evaluation results donut, a **non-compliant AI resources by account and Region heat map**, and two detail tables (per-resource and per rule evaluation) with status icons, all scoped to the latest snapshot. Dedicated dropdown controls filter the tracker section without affecting the charts above.

  The heat map is the account × Region cross-tab, so it replaces the separate account and Region compliance bars rather than sitting alongside them. It follows the same density heat map pattern used on the Config Usage Insights and Configuration Item Events tabs, with a grey-to-red gradient because it measures non-compliance.

All three AI tabs follow the core CRCD conventions: accounts are displayed using the shared `account-name-id` label (account name plus account ID in a single column), visuals carry detailed field-based tooltips, inventory tables are paginated, filter controls have info icons explaining what they do, and every KPI either carries a month-over-month sparkline with a comparison value or is deliberately pinned to the latest snapshot as a point-in-time figure.

### AI Agent Inventory

![CRCD](../images/ai-agent-inventory.png "AWS Config Dashboard, AI Agent Inventory")

Fleet view of Amazon Bedrock AgentCore Runtimes and the surrounding AI platform:

* **KPI row** — total agents, fully governed agents (guardrail attached AND IAM role assigned AND private network), and agents with governance gaps. These are pinned to the latest snapshot, so they are point-in-time figures rather than trends.
* **Agents by number of failing controls** — compound risk across all four controls, coloured green through red by severity. Note the deliberate difference in scope: this counts **four** controls including tracing, while the *fully governed* KPI counts the **three security** controls only, so the KPI reads higher. Agents that are secure but unobservable land in the one-gap band. Clicking a bar filters the sheet, including the agent roster.
* **Agent guardrail coverage by account** — stacked bar of agents with a guardrail attached versus agents running unprotected, per account. This is the actionable multi-account view: it identifies *which* accounts are deploying agents without safety controls, rather than reporting a single fleet-wide percentage.
* **Control gauges** — percentage of agents passing each control: guardrail coverage, IAM role assignment, network security, and tracing (observability). Traffic-light thresholds as above.
* **Agent fleet growth** — deployment timeline.
* **Models by guardrail coverage** — which foundation models run agents without safety controls.
* **AI platform estate** — full-width treemap of all recorded AI resource types (runtimes, knowledge bases, guardrails, gateways, memories, browsers, code interpreters, SageMaker resources). This treemap is the single source for per-resource-type counts; separate count tiles would only restate a subset of it. Coloured on a neutral grey-to-blue ramp because it measures volume, not compliance.
* **Agent roster** — every agent with its governance state as icon columns (guardrail, IAM, network, tracing), from the latest snapshot.

> [!note] Why the estate count exceeds "AI resources under governance"
> The estate treemap counts every recorded AI resource, while the AI Governance tab counts only resources that at least one AWS Config rule evaluates. The difference is made up entirely of `AWS::Bedrock::Guardrail` resources: guardrails are the control rather than the thing controlled, and none of the managed rules listed below targets a guardrail. Every other AI resource type is fully covered. This is a property of the current Config rule catalogue, not a gap in the deployment.

### AI Remediation Activity

![CRCD](../images/ai-remediation-activity.png "AWS Config Dashboard, AI Remediation Activity")

Finding backlog, resolution speed, and remediation progress. The underlying view computes a per-finding lifecycle (first seen, last seen, days open, open/resolved status) using window functions:

* **KPI row** — open findings, high-priority open findings, average days to resolve, and the age of the oldest open finding. Each carries a month-over-month sparkline and comparison value, so the reader sees whether the backlog is growing or shrinking rather than only its current size.
* **Findings by Config rule** — colored by priority (High for AgentCore, Medium for Bedrock and SageMaker).
* **Remediation trend by resource type** — non-compliant findings over time.
* **Remediation velocity** — findings resolved per week.
* **Open findings by age band** — open findings bucketed into 0–7, 8–30, 31–90 and 90+ days, split by priority. An average resolution time hides a stale backlog; this shows it directly.
* **Open finding backlog by age** — every open finding, oldest first, with first-seen date and days open.

Visuals with data dimensions support click-to-filter: selecting a data point filters every other visual on the same sheet. Each sheet also provides dropdown filters and a date range picker at the top.

## Data sources

The module adds four Amazon Athena views on top of the `cid_crcd_config` table:

| View | Content |
|------|---------|
| `v_ai_governance_compliance` | AWS Config rule evaluations targeting Bedrock, AgentCore, and SageMaker resources |
| `v_ai_governance_agents` | Bedrock AgentCore Runtime configuration items with guardrail, IAM, network, and tracing attributes (display-normalized values) |
| `v_ai_governance_remediation` | NON_COMPLIANT evaluations with priority classification and per-finding lifecycle columns (`first_seen`, `last_seen`, `days_open`, `finding_status`) |
| `v_ai_governance_inventory` | All AI resource types recorded by AWS Config, including AgentCore Gateway, Memory, Browser, and Code Interpreter |

Each view feeds one QuickSight SPICE dataset with a daily refresh schedule. The views guard against non-date partition values (`dt` must match `YYYY-MM-DD`), so environments that maintain a `latest` partition are not affected.

## Prerequisites

1. **CRCD deployed** — the module ships as part of the standard CRCD deployment (`cid-cmd deploy`). No separate installation step.
2. **AWS Config recording for AI resource types** — enable recording for the resource types you use:
   `AWS::Bedrock::Guardrail`, `AWS::Bedrock::KnowledgeBase`, `AWS::Bedrock::Prompt`, `AWS::Bedrock::ApplicationInferenceProfile`, `AWS::BedrockAgentCore::Runtime`, `AWS::BedrockAgentCore::Gateway`, `AWS::BedrockAgentCore::Memory`, `AWS::BedrockAgentCore::BrowserCustom`, `AWS::BedrockAgentCore::CodeInterpreterCustom`, `AWS::SageMaker::Model`, `AWS::SageMaker::EndpointConfig`.
3. **AWS Config rules evaluating AI resources** — the compliance visuals show data for whichever rules you deploy. Recommended starting set from the AWS Config managed rules:
   * [`BEDROCKAGENTCORE_RUNTIME_PRIVATE_NETWORK_REQUIRED`](https://docs.aws.amazon.com/config/latest/developerguide/bedrockagentcore-runtime-private-network-required.html)
   * [`BEDROCKAGENTCORE_GATEWAY_AUTHORIZER_ENABLED`](https://docs.aws.amazon.com/config/latest/developerguide/bedrockagentcore-gateway-authorizer-enabled.html)
   * `BEDROCKAGENTCORE_GATEWAY_ENCRYPTION_ENABLED` (rule `bedrockagentcore-gateway-encryption-enabled`, see [Security Hub control BedrockAgentCore.4](https://docs.aws.amazon.com/securityhub/latest/userguide/bedrockagentcore-controls.html))
   * [`BEDROCK_AGENTCORE_MEMORY_ENCRYPTION_ENABLED`](https://docs.aws.amazon.com/config/latest/developerguide/bedrock-agentcore-memory-encryption-enabled.html)
   * `BEDROCKAGENTCORE_BROWSERCUSTOM_NETWORK_MODE_NOT_PUBLIC` (rule `bedrockagentcore-browsercustom-network-mode-not-public`, see [Security Hub control BedrockAgentCore.5](https://docs.aws.amazon.com/securityhub/latest/userguide/bedrockagentcore-controls.html))
   * [`BEDROCKAGENTCORE_CODEINTERPRETER_NETWORKMODE_CHECK`](https://docs.aws.amazon.com/config/latest/developerguide/bedrockagentcore-codeinterpreter-networkmode-check.html)
   * [`BEDROCK_DATA_SOURCE_ENCRYPTION_ENABLED`](https://docs.aws.amazon.com/config/latest/developerguide/bedrock-data-source-encryption-enabled.html)
   * [`SAGEMAKER_MODEL_PRIVATE_REGISTRY_REQUIRED`](https://docs.aws.amazon.com/config/latest/developerguide/sagemaker-model-private-registry-required.html)
   * [`SAGEMAKER_ENDPOINT_CONFIG_KMS_KEY_REQUIRED`](https://docs.aws.amazon.com/config/latest/developerguide/sagemaker-endpoint-config-kms-key-required.html)

   Managed rule availability varies by AWS Region — several of the AgentCore rules are available in a limited set of Regions. Check the linked documentation for each rule before relying on it.
4. **Custom rules for controls without managed equivalents** — guardrail attachment and agent IAM role checks require custom AWS Config rules (for example `agentcore-runtime-guardrail-attached` and `agentcore-runtime-iam-role-check`). The AI Governance: Hands-On Controls Workshop provides working CloudFormation templates for these.

If no AI resources are recorded by AWS Config, the AI tabs render without data. The rest of the dashboard is unaffected.

## Upgrading from an earlier deployment

`cid-cmd deploy` does **not** replace Athena views that already exist. If you upgrade a CRCD deployment that already contains an earlier version of the AI views, drop them first so the deployment recreates them with the current definition:

```sql
DROP VIEW IF EXISTS v_ai_governance_compliance;
DROP VIEW IF EXISTS v_ai_governance_agents;
DROP VIEW IF EXISTS v_ai_governance_remediation;
DROP VIEW IF EXISTS v_ai_governance_inventory;
```

Then run `cid-cmd deploy` again and trigger a full SPICE refresh of the four `ai-governance-*` datasets. Skipping this step leaves the datasets bound to stale view definitions, which can break dashboard visuals after the dataset refresh.

## Empty state

Customers who have not yet deployed AI workloads, or have not enabled AWS Config recording for AI resource types, will see empty visuals on the three AI tabs. This is expected. The visuals populate automatically once AWS Config delivers the first snapshot containing AI resources — no dashboard change is required.
