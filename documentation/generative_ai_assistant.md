# AWS Config Dashboard and Amazon Quick generative AI assistant

## Feature overview
This setup combines your AWS Config dashboard with Amazon Quick's generative AI capabilities to create a compliance chat agent that understands your environment and provides contextual insights. 

You will need an Amazon Quick user with Author Pro or Reader Pro permissions, see [Managing users in Amazon QuickSight](https://docs.aws.amazon.com/quicksight/latest/user/managing-users.html) for setup instructions. Amazon Quick generative AI features incur additional charges. Review Author Pro, Reader Pro and infrastructure fee [Amazon QuickSight](https://aws.amazon.com/quicksight/pricing/) pricing before proceeding.

## Deployment

### Step 1: Create a Space 
1. Navigate to Quick Spaces
   1. Open Amazon Quick console 
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
   1. In the Quick console, select "Chat Agents" 
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

### Step 3: Configure the agent
Add this in the "Configuration" field:

```
You are an AWS Config security specialist with a compliance-first mindset. You measure organizational compliance, assess risks, and provide cost-effective security solutions.

Focus on compliance monitoring, resource management, and AWS Config cost optimization. Always consider risk levels and provide mitigation strategies. Balance security needs with cost efficiency. 

Tone: Professional, authoritative, and security-focused. Communicate with confidence while being thorough in compliance analysis.

Response length: Comprehensive enough to cover all relevant data while remaining focused and actionable.
```


### Step 4: Upload Reference Document
1. In the "Reference document" section, click "Upload Files"
1. Upload the file [crcd_chat_agent_reference.md](./crcd_chat_agent_reference.md) provided in this repository

This document contains the agent's step-by-step methodology, response templates, constraints, and example interactions.

### Step 5: Link knowledge sources
1. Connect the CRCD Dashboard Space 
   1. Scroll to "Knowledge sources" section 
   1. Click "Link spaces" 
   1. Select your CRCD Dashboard Space 
   1. Click "Link" 

### Step 6: Customization 
1. Add this Welcome message:
   ```
   Hello! I'm your AWS Config Compliance Expert. I can help you analyze compliance posture, review resource configurations, and optimize AWS Config costs. 
   ```
1. Add these Suggested Prompts:
   ```
   Show me the current compliance status across all AWS accounts
   How many EC2 instances are running on us-east-1?
   ```

### Step 7:
1. Review and Launch 
   1. Verify all configuration is correct 
   1. Click "Launch Chat Agent"

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

Next example assumes you have tagged your resources with a tag named "Owner" and a value of "Alpha". 

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
