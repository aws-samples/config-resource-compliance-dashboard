# Deployment Trade-offs for the Published Conformance Pack

## Context

We have the CRCD conformance pack ready for publication in the official [AWS Config conformance pack sample templates library](https://docs.aws.amazon.com/config/latest/developerguide/conformancepack-sample-templates.html). This document outlines the deployment choices available to customers and their trade-offs, to inform the conversation about what we recommend and document.

## What We Prepared

### Original Approach (`crcd-conformance-pack-stack.yaml`)

The existing CRCD project deploys the conformance pack via a single CloudFormation template that handles everything for the customer:
- Deploys all 16 rules (10 managed + 4 IAM managed + 2 custom Lambda) across all specified regions using StackSets.
- Automatically skips rules that are unsupported in specific regions (hard-coded regional availability conditions).
- Deploys IAM-related rules (including custom Lambdas) in a single region only, avoiding duplication of global resource evaluations.
- Creates all prerequisite resources (Lambda functions, IAM roles, log groups, S3 bucket for template storage) as part of the same stack.
- Supports both standalone and AWS Organizations deployment modes from a single template.
- Cannot be published in the conformance pack library — it's a CloudFormation orchestration stack, not a conformance pack template.

We extracted two publishable conformance pack templates from this.

### For Publication: Base Template (`crcd-conformance-pack-template.yaml`)

- **10 AWS Config managed rules** covering S3 protection, EC2 IMDSv2, and security group port restrictions.
- **No prerequisites** — can be deployed directly from the AWS Config console dropdown or via CLI.
- **Console dropdown eligible** — since it has no Lambda dependencies, the Conformance Packs team can make it available in the Config console's "Use sample template" dropdown for one-click deployment.

### For Publication: Extended Template (`crcd-conformance-pack-template-extended.yaml`)

- **14 AWS Config managed rules** (the 10 rules in the base template + 4 IAM managed rules: root MFA, root access key, user MFA, console MFA).
- **2 custom Lambda-based rules** (root account not used regularly, IAM user access key check) — these are our key differentiators that don't exist in any other published pack.
- **Requires prerequisites** — customers must first deploy `crcd-conformance-pack-prerequisites.yaml` (a CloudFormation template that creates the Lambda functions and IAM roles).
- **NOT eligible for the console dropdown** — per the Conformance Packs team's [onboarding wiki](https://w.amazon.com/bin/view/AWS/Config/Compliance/Overwatch/Overview/ConformsOnboarding): "if your template expects some prerequisite resources to be present when it gets deployed, such as any lambda functions (in case of custom rules), then it cannot be currently made available through the drop-down on the Conformance Pack Deployment page." It would only be available as a downloadable template from the AWS documentation page.
- **No published precedent** — our research found no currently published conformance pack template (on the AWS docs page or GitHub repo) that uses custom Lambda rules. The only example is a generic `custom-conformance-pack.yaml` sample on GitHub. If published, ours would be the first.

---

## Option A: Deploy the Extended Template in All Regions

**How it works:** Customer deploys the prerequisites (Lambda functions) and the extended conformance pack in every region where AWS Config is enabled.

| Aspect | Assessment |
|--------|-----------|
| **Simplicity** | Moderately complex — requires deploying prerequisites in every region, then the extended conformance pack in every region. More steps than the original approach, but uniform (same process everywhere) |
| **Coverage** | Full coverage: S3, EC2, security groups, and IAM in every region |
| **Cost** | Highest — custom Lambda functions are duplicated in every region and invoked daily in each, producing redundant results since they check IAM and account-level resources that are global. IAM managed rule evaluations are equally redundant |
| **Precedent** | The published "Operational Best Practices for AWS Identity and Access Management" pack does exactly this — no special handling for global resources |
| **Regional availability** | Risk of deployment failure in regions where certain rules aren't supported. Customer must manually remove unsupported rules. This is how all published templates work — the [official guidance](https://docs.aws.amazon.com/config/latest/developerguide/conformancepack-sample-templates.html) states: "It is recommended that you review the rules available in the region where you deploy a conformance pack and amend the template for rules not yet available in that region before deploying." |
| **Prerequisites** | Must deploy Lambda prerequisites in every region |

**Best for:** Nothing. Option B has similar deployment complexity and avoids redundancy.

**Discoverability concern:** There is no apparent mechanism to guide customers from the YAML template to the deployment documentation. The published artifact is a YAML file on GitHub — we can add a link to the documentation in the template's comment header, but there is no guarantee customers will follow it. They may download the template and deploy it however they are used to, skipping the prerequisites entirely, which would cause deployment failures for the custom Lambda rules.

---

## Option B: Extended Template in One Region + Base Template in All Others

**How it works:** Customer deploys the extended template (with Lambdas + IAM rules) in a single "primary" region, then deploys the base template (managed rules only, no Lambdas) in all other regions.

| Aspect | Assessment |
|--------|-----------|
| **Simplicity** | Moderately complex — requires understanding which template goes where and following closely our instructions |
| **Coverage** | Full coverage: IAM checked once globally, regional resources checked in each region |
| **Cost** | Optimized — Same as our original approach: Lambda functions and IAM evaluations run once, not duplicated |
| **Precedent** | This is what our current `crcd-conformance-pack-stack.yaml` does under the hood |
| **Regional availability** | Same risk as Option A for the base template in newer regions |
| **Prerequisites** | Only needed in the primary region |

**Best for:** Cost-conscious customers or large organizations with many regions enabled. Our Conformance Pack is published on the sample template library.

**Discoverability concern:** Same as Option A — customers need to find and follow the documentation to understand the split deployment approach. A YAML template on GitHub with a link in the header comment is the only touchpoint. Customers unfamiliar with this pattern may deploy the extended template everywhere (falling into Option A) or deploy the base template everywhere (losing the IAM rules), depending on which file they download.

**Publishing risk:** This option requires getting two very similar conformance pack templates approved and published. The Conformance Packs team may push back on publishing two near-identical templates for the same pack, or the documentation team may question why two variants exist. This adds review friction and ongoing maintenance burden (any rule change must be applied to both templates).

---

## Option C: Base Template Only (All Regions)

**How it works:** Customer deploys only the base template (managed rules, no custom Lambdas) in all regions.

| Aspect | Assessment |
|--------|-----------|
| **Simplicity** | Simplest — no prerequisites at all, can deploy from console dropdown |
| **Coverage** | Partial — no IAM custom rules (root usage check, access key check). IAM managed rules (MFA, root access key) are also excluded |
| **Cost** | Lowest — only managed rules, no Lambda invocations |
| **Precedent** | Exactly how all other published packs work |
| **Regional availability** | Same risk in newer regions |
| **Prerequisites** | None |
| **Differentiation** | Weak — the rules are a subset of existing published packs |

**Best for:** Maximum adoption via console dropdown, but sacrifices what makes this pack unique.

---

## Option D: Use the Full CRCD CloudFormation Stack (Current Approach)

**How it works:** Customer deploys `crcd-conformance-pack-stack.yaml` which handles everything: StackSets for multi-region, regional availability conditions, IAM rules in one region, and conformance pack deployment.

| Aspect | Assessment |
|--------|-----------|
| **Simplicity** | One-click deployment — handles all complexity for the customer |
| **Coverage** | Full coverage with no duplication |
| **Cost** | Optimized — IAM rules in one region, regional rules everywhere, no unnecessary Lambda duplication |
| **Precedent** | Not publishable in the conformance pack library (it's a CloudFormation stack, not a conformance pack template) |
| **Regional availability** | Handled automatically — conditions skip unsupported rules per region |
| **Prerequisites** | All bundled within the stack |

**Best for:** The ideal customer experience, but cannot be published in the conformance pack library.

---

## Comparison Matrix

| | Option A (Extended everywhere) | Option B (Extended + Base split) | Option C (Base only) | Option D (CRCD Stack) |
|---|---|---|---|---|
| **Console dropdown** | No | Only the base template | Yes | No |
| **Config sample templates page** | Yes | Yes | Yes | No (separate project) |
| **Regional availability handling** | Manual | Manual | Manual | Automatic |
| **IAM custom rules** | Yes (all regions) | Yes (one region) | No | Yes (one region) |
| **Lambda prerequisites deployment** | Every region | One region | None | Bundled |
| **Multi-region cost** | Highest | Optimized | Low | Optimized |
| **Customer effort** | High | Highest | Medium | Lowest |
| **Uniqueness/differentiation** | Strong | Strong | Weak | Strong |
| **Publishable in library** | Yes | Yes (2 templates) | Yes | No |

---

## Key Questions for Discussion

1. **Do we publish the extended template, the base, or both?**
   - Extended only = stronger differentiation, no dropdown
   - Base only = dropdown placement, weak differentiation
   - Both = maximum flexibility, more documentation/maintenance

2. **Do we recommend Option A or Option B for multi-region?**
   - Option A is simpler to explain but costs more and duplicates evaluations
   - Option B is what we do internally but harder to communicate
   - The published AWS IAM pack uses Option A implicitly (no guidance on this)

3. **Do we keep the full CRCD stack as the "recommended" deployment path?**
   - It handles regional availability automatically — published templates can't
   - It avoids duplication — published templates don't attempt this
   - Risk: maintaining two deployment paths (published template + CRCD stack)

4. **Are we comfortable with deployment failures in unsupported regions?**
   - No published pack solves this — the official guidance is "check before deploying"
   - Our target audience (beginners) may not know how to handle this
   - Mitigation: document which rules to remove per region, or keep pointing to the CRCD stack


