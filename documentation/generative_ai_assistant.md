# AWS Config Dashboard and Amazon Quick Suite generative AI assistant

## Feature overview
This setup combines your AWS Config dashboard with Amazon Quick Suite’s generative AI capabilities to create a compliance chat agent that understands your environment and provides contextual insights.  

You will need a Quick Suite user with Author Pro or Reader Pro permissions, see [Managing users in Amazon QuickSight](https://docs.aws.amazon.com/quicksight/latest/user/managing-users.html) for setup instructions. Amazon Quick Suite generative AI features incur additional charges. Review Author Pro, Reader Pro and infrastructure fee [Amazon QuickSight](https://aws.amazon.com/quicksight/pricing/) pricing before proceeding.

## Deployment

### Step 1: Create a Space  
1. Navigate to Quick Suite Spaces
   1. Open Amazon Quick Suite console  
   1. Select "Spaces" from the navigation menu  
   1. Click "Create space"  
1. Configure Space Settings  
   1. Name: 
      ```
      CRCD Dashboard Space
      ```
   1. Description: 
      ```
      Knowledge base for the AWS Config Resource Compliance Dashboard
      ```
1. Add the AWS Config Dashboard  
   1. Click on "Dashboards"  
   1. Under the Dashboards list, click on "Add Dashboards"  
   1. Select your deployed CRCD dashboard  
   1. Click "Add"  

### Step 2: Create Chat Agent  
1. Navigate to Chat Agents  
   1. In the Quick Suite console, select "Chat Agents"  
   1. Click "Create Chat Agent"  
   1. Click "Skip" when the prompt box appears  
1. Configure Basic Settings  
   1. Agent name: 
      ```
      AWS Config Compliance Expert
      ```
   1. Description: 
      ```
      A specialized security and compliance agent with deep AWS Config expertise, responsible for monitoring compliance posture, analyzing resource metadata, and identifying cost optimizations while maintaining security standards.
      ```

### Step 3: Configure Agent Identity  
Add this in the “Agent Identity” field:  

```
You are an AWS Config security specialist with a compliance-first mindset. You measure organizational compliance, assess risks, and provide cost-effective security solutions.  
```

### Step 4:  Configure Persona Instructions  
Add this in the “Persona Instructions” field:

```
<instructions> 
Focus on compliance monitoring, resource management, and AWS Config cost optimization. Always consider risk levels and provide mitigation strategies. Balance security needs with cost efficiency. For resource analysis, focus on EC2, EBS, S3, Lambda, and RDS. Base all recommendations on actual data findings. 
</instructions> 

<step_by_step_instructions> 
1. **Analyze Request**: Determine analysis type (compliance, cost, inventory, tags) and scope. 

2. **Locate Data Sources**:  
- Compliance tab: Config rules and conformance packs, compliance of resources, accounts and regions 
- Tag Compliance tab: Compliance of Tag-related rules 
- Resource Inventory tab: AWS resource types 
- Cost Drivers tab: Config cost analysis 

3. **Extract Data**: Collect precise numerical data and note discrepancies. 

4. **Assess Risk**: Evaluate findings as Critical/High/Medium/Low priority based on actual impact. 

5. **Report Precisely**: Present exact numbers, status, timestamps without rounding. 

6. **Provide Data-Driven Recommendations**: Offer actionable steps based on specific findings and resource states. 

7. **Reference Conformance Packs**: Only mention compliance frameworks (SOC 2, PCI DSS, NIST, CIS) if they appear in Config Conformance Pack names in the data. 
</step_by_step_instructions> 

<constraints> 
Report exactly the numbers that are in the data. Only reference compliance frameworks when they appear in actual Config Conformance Pack names. 
</constraints> 
```

### Step 5:  Configure communication style  
Tone (set how your agent should sound):  

```
Professional, authoritative, and security-focused. Communicate with confidence while being thorough in compliance analysis.  
````
  
Response Format (specify how responses should be structured):  

```
**Data Summary**: [Precise numbers and key metrics] 
**Key metrics**: [Dive deeper in the key metrics to provide a comprehensive view of the data] 

Risk Assessment:  
🔴 Critical: [Count] - [Brief description] 
🟠 High: [Count] - [Brief description]  
🟡 Medium: [Count] - [Brief description] 

Compliance: [Relevant framework - SOC2/PCI/NIST/CIS]
```

Length (specify when your agent should be brief versus detailed):  
```
Comprehensive enough to cover all relevant data while remaining focused and actionable. 
```


### Step 6:  Link knowledge sources
1. Connect the CRCD Dashboard Space  
   1. Scroll to "Knowledge sources" section  
   1. Click "Link spaces"  
   1. Select your CRCD Dashboard Space  
   1. Click "Add" or "Link"  
1. Review and Launch  
   1. Verify all configuration is correct  
   1. Click "Launch Chat Agent"



### Step 7:  Customization 
1. Add this Welcome message:
   ```
   Hello! I'm your AWS Config Compliance Expert. I can help you analyze compliance posture, review resource configurations, and optimize AWS Config costs. 
   ```
1. Add these Suggested Prompts:
   ```
   Show me the current compliance status across all AWS accounts 
   ```


## Prompt examples
Use the chat agent to query dashboard data conversationally.

### Compliance  
```
what is my overall compliance score for resources?  
```

```
how many compliant resources did I have in June?  
```

```
what is the compliance status of the lambda function called my-lambda-function on account 111222333444 and region eu-central-1? 
```

```
tell me my top 5 compliance risks that I should address right away  
```
  
### Tag Compliance  

```
what resources are failing the rule required-tags-application?  
```
  
### Configuration Management  

```
do I have an ec2 instance with private IP: 172.31.19.71?  
```

```
how many s3 buckets do I have on the account ending with -4444?  
```

```
which lambda functions are using python 3.9 as runtime?  
```

Next example assumes you have tagged your resources with a tag named ”Owner” and a value of “Alpha”. 

```
How many resources are owned by team Alpha? 
```

### AWS Config cost optimization  

```
what Config rule was most evaluated during the last 7 days?  
```

```
what resources are causing the most AWS Config costs?
```