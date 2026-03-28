"""Terraform module test generators, validation, and scoring."""

from typing import Dict, List

from Asgard.Volundr.Terraform.models.terraform_models import (
    CloudProvider,
    ModuleConfig,
)


def generate_tests(config: ModuleConfig) -> Dict[str, str]:
    tests: Dict[str, str] = {}
    output_name = config.outputs[0].name if config.outputs else "id"
    terratest_content = f'''package test

import (
    "testing"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func Test{config.name.replace("_", "").title()}Basic(t *testing.T) {{
    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{{
        TerraformDir: "../examples/basic",
    }})

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    output := terraform.Output(t, terraformOptions, "{output_name}")
    assert.NotEmpty(t, output)
}}
'''
    tests["terratest"] = terratest_content
    kitchen_yml = f'''---
driver:
  name: terraform
  variable_files:
    - testing.tfvars

provisioner:
  name: terraform

verifier:
  name: terraform
  format: junit

platforms:
  - name: {config.provider.value}

suites:
  - name: {config.name}
    driver:
      root_module_directory: test/fixtures/{config.name}
    verifier:
      color: false
      fail_fast: false
      systems:
        - name: {config.name}
          backend: local
'''
    tests["kitchen"] = kitchen_yml
    return tests


def validate_module(module_files: Dict[str, str], config: ModuleConfig) -> List[str]:
    issues: List[str] = []
    for file in ["main.tf", "variables.tf", "outputs.tf", "versions.tf"]:
        if file not in module_files:
            issues.append(f"Missing required file: {file}")
    if "variables.tf" in module_files:
        variables_content = module_files["variables.tf"]
        for var in config.variables:
            if f'variable "{var.name}"' not in variables_content:
                issues.append(f"Variable {var.name} not found in variables.tf")
    if "outputs.tf" in module_files:
        outputs_content = module_files["outputs.tf"]
        for output in config.outputs:
            if f'output "{output.name}"' not in outputs_content:
                issues.append(f"Output {output.name} not found in outputs.tf")
    if "main.tf" in module_files:
        main_content = module_files["main.tf"]
        if config.provider == CloudProvider.AWS:
            if "aws_s3_bucket" in main_content and "server_side_encryption" not in main_content:
                issues.append("S3 bucket missing encryption configuration")
            if "aws_security_group" in main_content and "0.0.0.0/0" in main_content:
                issues.append("Security group allows access from 0.0.0.0/0")
    return issues


def calculate_best_practice_score(module_files: Dict[str, str], config: ModuleConfig) -> float:
    score = 0.0
    max_score = 0.0
    max_score += 25
    required_files = ["main.tf", "variables.tf", "outputs.tf", "versions.tf", "README.md"]
    present_files = sum(1 for file in required_files if file in module_files)
    score += (present_files / len(required_files)) * 25
    max_score += 20
    if config.variables:
        documented_vars = sum(1 for var in config.variables if var.description)
        score += (documented_vars / len(config.variables)) * 20
    else:
        score += 20
    max_score += 15
    if config.outputs:
        documented_outputs = sum(1 for output in config.outputs if output.description)
        score += (documented_outputs / len(config.outputs)) * 15
    else:
        score += 15
    max_score += 15
    if "versions.tf" in module_files:
        versions_content = module_files["versions.tf"]
        if "required_version" in versions_content:
            score += 8
        if "required_providers" in versions_content:
            score += 7
    max_score += 15
    if "main.tf" in module_files:
        main_content = module_files["main.tf"]
        if config.provider == CloudProvider.AWS:
            if "encryption" in main_content or "kms" in main_content:
                score += 8
            if "0.0.0.0/0" not in main_content:
                score += 7
        else:
            score += 15
    max_score += 10
    if "README.md" in module_files:
        readme_content = module_files["README.md"]
        if len(readme_content) > 1000:
            score += 10
        elif len(readme_content) > 500:
            score += 5
    return (score / max_score) * 100 if max_score > 0 else 0.0
