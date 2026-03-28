"""Terraform resource and data source block generators + example generation."""

import json
from typing import Dict, List

from Asgard.Volundr.Terraform.models.terraform_models import (
    CloudProvider,
    ModuleComplexity,
    ModuleConfig,
)

PROVIDER_SOURCES = {
    CloudProvider.AWS: ("hashicorp/aws", ">= 5.0"),
    CloudProvider.AZURE: ("hashicorp/azurerm", ">= 3.0"),
    CloudProvider.GCP: ("hashicorp/google", ">= 4.0"),
    CloudProvider.KUBERNETES: ("hashicorp/kubernetes", ">= 2.0"),
    CloudProvider.HELM: ("hashicorp/helm", ">= 2.0"),
    CloudProvider.VAULT: ("hashicorp/vault", ">= 3.0"),
}


def generate_data_source_block(data_source: str, config: ModuleConfig) -> List[str]:
    lines: List[str] = []
    if config.provider == CloudProvider.AWS:
        if "vpc" in data_source.lower():
            lines.extend(['data "aws_vpc" "default" {', "  default = true", "}"])
        elif "subnet" in data_source.lower():
            lines.extend([
                'data "aws_subnets" "default" {', "  filter {",
                '    name   = "vpc-id"', "    values = [data.aws_vpc.default.id]",
                "  }", "}",
            ])
        elif "ami" in data_source.lower():
            lines.extend([
                'data "aws_ami" "latest" {', "  most_recent = true",
                '  owners      = ["amazon"]', "", "  filter {",
                '    name   = "name"',
                '    values = ["amzn2-ami-hvm-*-x86_64-gp2"]', "  }", "}",
            ])
    elif config.provider == CloudProvider.AZURE:
        if "resource_group" in data_source.lower():
            lines.extend([
                'data "azurerm_resource_group" "main" {',
                "  name = var.resource_group_name", "}",
            ])
    elif config.provider == CloudProvider.GCP:
        if "project" in data_source.lower():
            lines.extend(['data "google_project" "current" {', "}"])
    return lines


def generate_resource_block(resource: str, config: ModuleConfig) -> List[str]:
    lines: List[str] = []
    tags_ref = "local.common_tags" if config.tags else "var.tags"
    if config.provider == CloudProvider.AWS:
        if "instance" in resource.lower():
            lines.extend([
                'resource "aws_instance" "main" {',
                "  ami           = data.aws_ami.latest.id",
                "  instance_type = var.instance_type",
                "  subnet_id     = data.aws_subnets.default.ids[0]", "",
                f"  tags = merge({tags_ref}, {{",
                "    Name = var.instance_name", "  })", "}",
            ])
        elif "s3" in resource.lower():
            lines.extend([
                'resource "aws_s3_bucket" "main" {',
                "  bucket = var.bucket_name", "",
                f"  tags = {tags_ref}", "}", "",
                'resource "aws_s3_bucket_versioning" "main" {',
                "  bucket = aws_s3_bucket.main.id",
                "  versioning_configuration {",
                '    status = "Enabled"', "  }", "}", "",
                'resource "aws_s3_bucket_server_side_encryption_configuration" "main" {',
                "  bucket = aws_s3_bucket.main.id", "", "  rule {",
                "    apply_server_side_encryption_by_default {",
                '      sse_algorithm = "AES256"', "    }", "  }", "}",
            ])
        elif "vpc" in resource.lower():
            lines.extend([
                'resource "aws_vpc" "main" {',
                "  cidr_block           = var.vpc_cidr",
                "  enable_dns_hostnames = true",
                "  enable_dns_support   = true", "",
                f"  tags = merge({tags_ref}, {{",
                '    Name = "${var.name_prefix}-vpc"', "  })", "}",
            ])
    elif config.provider == CloudProvider.AZURE:
        if "resource_group" in resource.lower():
            lines.extend([
                'resource "azurerm_resource_group" "main" {',
                "  name     = var.resource_group_name",
                "  location = var.location", "",
                "  tags = var.tags", "}",
            ])
        elif "virtual_network" in resource.lower():
            lines.extend([
                'resource "azurerm_virtual_network" "main" {',
                '  name                = "${var.name_prefix}-vnet"',
                "  address_space       = [var.vnet_cidr]",
                "  location            = azurerm_resource_group.main.location",
                "  resource_group_name = azurerm_resource_group.main.name", "",
                "  tags = var.tags", "}",
            ])
    elif config.provider == CloudProvider.GCP:
        if "compute_instance" in resource.lower():
            lines.extend([
                'resource "google_compute_instance" "main" {',
                "  name         = var.instance_name",
                "  machine_type = var.machine_type",
                "  zone         = var.zone", "",
                "  boot_disk {", "    initialize_params {",
                "      image = var.image", "    }", "}", "",
                "  network_interface {", '    network = "default"',
                "    access_config {}", "}", "",
                "  labels = var.labels", "}",
            ])
    return lines


def generate_examples(config: ModuleConfig) -> Dict[str, str]:
    examples: Dict[str, str] = {}
    basic_example: List[str] = [
        f'module "{config.name}_basic" {{', '  source = "../../"', "",
    ]
    for var in config.variables:
        if var.default is None:
            if "name" in var.name.lower():
                basic_example.append(f'  {var.name} = "example-{config.name}"')
            elif var.type == "string":
                basic_example.append(f'  {var.name} = "example-value"')
            elif var.type == "number":
                basic_example.append(f"  {var.name} = 1")
            elif var.type == "bool":
                basic_example.append(f"  {var.name} = true")
    basic_example.append("}")
    examples["basic"] = "\n".join(basic_example)
    if config.complexity in [ModuleComplexity.COMPLEX, ModuleComplexity.ENTERPRISE]:
        advanced_example: List[str] = [
            f'module "{config.name}_advanced" {{', '  source = "../../"', "",
        ]
        for var in config.variables:
            if var.default is not None:
                if isinstance(var.default, str):
                    advanced_example.append(f'  {var.name} = "advanced-{var.default}"')
                else:
                    advanced_example.append(f"  {var.name} = {json.dumps(var.default)}")
            else:
                advanced_example.append(f'  {var.name} = "advanced-example"')
        advanced_example.append("}")
        examples["advanced"] = "\n".join(advanced_example)
    return examples
