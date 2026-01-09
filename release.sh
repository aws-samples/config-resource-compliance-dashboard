#!/bin/bash

aws s3 cp ./cloudformation/cid-crcd-resources.yaml  s3://aws-managed-cost-intelligence-dashboards/cfn/cid-crcd-resources.yaml
aws s3 cp ./cirt/crcd-cirt-conformance-pack.yaml    s3://aws-managed-cost-intelligence-dashboards/cfn/crcd-cirt-conformance-pack.yaml