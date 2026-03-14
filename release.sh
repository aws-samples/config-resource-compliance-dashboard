#!/bin/bash

aws s3 cp ./cloudformation/cid-crcd-stack.yaml s3://aws-managed-cost-intelligence-dashboards/cfn/cid-crcd-stack.yaml
# aws s3 cp ./cloudformation/cid-crcd-resources.yaml s3://aws-managed-cost-intelligence-dashboards/cfn/cid-crcd-resources.yaml
aws s3 cp ./crcd_conformance_pack/crcd-conformance-pack-stack.yaml s3://aws-managed-cost-intelligence-dashboards/cfn/crcd-conformance-pack-stack.yaml
aws s3 cp  ./backfill/crcd-backfill-resources.yaml   s3://aws-managed-cost-intelligence-dashboards/cfn/crcd-backfill-resources.yaml
