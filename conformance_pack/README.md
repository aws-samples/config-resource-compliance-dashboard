# Threat-Informed Security Posture with AWS Security Incident Response

The [AWS Security Incident Response](https://aws.amazon.com/security-incident-response/) team is a specialized 24/7 global team that provides proactive and reactive security support to AWS customers for security responsibilities on the customer side of the [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/). When AWS Security Incident Response security engineers support a customer, they will help triage security findings and assist during potential active security events in the customer's AWS environment. They provide security recommendations and best practices to help prevent future security incidents.

This feature of the AWS Config Dashboard was developed in collaboration with AWS Security Incident Response security experts, drawing on their multi-year experience supporting AWS customers during active security incidents. It uses AWS Config rules recommended by security engineers to identify preventable, common misconfigurations that are known to create vulnerabilities exploited in attacks against AWS environments. Addressing these misconfigurations helps eliminate the low-hanging fruit that bad actors frequently target when attempting to gain unauthorized access.

**Please note:** Resolving these misconfigurations significantly reduces your attack surface, but does not guarantee complete protection against security incidents. Additional security controls, monitoring, and practices are recommended as part of a comprehensive security strategy.


## CRCD Threat-Informed Conformance Pack 

_**Please note:** The AWS Config conformance pack that bundles all recommended rules into a single deployable unit is under development. However, the dashboard's Threat-Informed Security Compliance tab is fully functional today — it displays compliance status for the standard AWS Config managed rules recommended by AWS Security Incident Response security engineers. You can deploy these rules individually in your environment and the dashboard will report on them regardless of whether they are deployed through other conformance packs or as standalone rules._


The AWS Config Resource Compliance Dashboard Threat-Informed Conformance Pack is a comprehensive compliance monitoring solution that deploys the AWS Config rules recommended by Security Incident Response Service security engineers.

![CRCD](../images/crcd-known-threat-exposures.png "AWS Config Dashboard, Threat-Informed Security Compliance tab")

The **Threat-Informed Security Compliance** tab will display compliance status of the [standard and custom AWS Config rules](./crcd-conformance-pack-specification.md) in the conformance pack. The dashboard classifies AWS Config rules according to the tactics and techniques presented in the [Threat Technique Catalog for AWS](https://aws-samples.github.io/threat-technique-catalog-for-aws/). The catalog is based on MITRE ATT&CK® and is used to identify and categorize threat actor behaviors observed by AWS. If you do not install the conformance pack, the dashboard will still display compliance of the [recommended standard AWS Config rules](./crcd-conformance-pack-specification.md) that you may have already deployed.



### Features
- **Recommended Rules**: Includes standard AWS Config managed rules and custom Lambda-based rules recommended by AWS Security Incident Response security engineers.
- **Threat Technique Catalog Classification**: Each rule is classified according to the Threat Technique Catalog for AWS (based on MITRE ATT&CK®).
- **Flexible Deployment**: Supports both AWS Organizations (organization-wide deployment) and standalone AWS accounts.
- **Multi-Region Support**: Deploys across all AWS Regions where AWS Config is enabled.
- **Automatic Updates**: In case of organization-wide deployment, new accounts joining the AWS Organization automatically receive the conformance pack.


# References
- [Threat Technique Catalog for AWS](https://aws-samples.github.io/threat-technique-catalog-for-aws/).
- [MITRE ATT&CK® Framework](https://attack.mitre.org/).
- [AWS Config Rules](https://docs.aws.amazon.com/config/latest/developerguide/managed-rules-by-aws-config.html).
- [AWS Security Incident Response service](https://aws.amazon.com/security-incident-response/).
- [Specification of all AWS Config and custom rules](./crcd-conformance-pack-specification.md) that will be deployed as part of the conformance pack.
