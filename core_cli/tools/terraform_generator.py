"""
TerraformGenerator - Terraform Infrastructure-as-Code Generation

Generates complete Terraform configurations for AWS, Azure, GCP, and on-premise
deployments with modules, variables, outputs, and best practices.
"""

import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid


class CloudProvider(Enum):
    """Supported cloud providers"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class ComputeType(Enum):
    """Compute resource types"""
    EC2 = "ec2"
    ECS = "ecs"
    EKS = "eks"
    VIRTUAL_MACHINE = "virtual_machine"
    GKE = "gke"
    APP_ENGINE = "app_engine"


class DatabaseType(Enum):
    """Database types"""
    RDS_POSTGRES = "rds_postgres"
    RDS_MYSQL = "rds_mysql"
    DYNAMODB = "dynamodb"
    COSMOS_DB = "cosmos_db"
    CLOUD_SQL = "cloud_sql"
    FIRESTORE = "firestore"


class StorageType(Enum):
    """Storage types"""
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"


@dataclass
class NetworkConfig:
    """Network configuration"""
    vpc_cidr: str = "10.0.0.0/16"
    public_subnet_cidrs: List[str] = field(default_factory=lambda: ["10.0.1.0/24", "10.0.2.0/24"])
    private_subnet_cidrs: List[str] = field(default_factory=lambda: ["10.0.10.0/24", "10.0.11.0/24"])
    enable_nat_gateway: bool = True
    enable_vpn: bool = False


@dataclass
class ComputeConfig:
    """Compute configuration"""
    compute_type: ComputeType
    instance_type: str = "t3.medium"
    desired_capacity: int = 3
    min_capacity: int = 2
    max_capacity: int = 10
    enable_autoscaling: bool = True
    ami: Optional[str] = None


@dataclass
class DatabaseConfig:
    """Database configuration"""
    database_type: DatabaseType
    db_name: str = "app_db"
    engine_version: str = "14.7"
    instance_class: str = "db.t3.medium"
    allocated_storage: int = 20
    enable_backup: bool = True
    backup_retention: int = 30
    enable_multi_az: bool = True
    publicly_accessible: bool = False


@dataclass
class TerraformConfig:
    """Complete Terraform configuration"""
    config_id: str
    project_name: str
    cloud_provider: CloudProvider
    region: str
    environment: str = "production"
    network_config: NetworkConfig = field(default_factory=NetworkConfig)
    compute_config: Optional[ComputeConfig] = None
    database_configs: Dict[str, DatabaseConfig] = field(default_factory=dict)
    storage_configs: Dict[str, str] = field(default_factory=dict)
    enable_monitoring: bool = True
    enable_logging: bool = True
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class TerraformGenerator:
    """
    Terraform Infrastructure-as-Code Generator
    
    Generates complete Terraform configurations for multiple cloud providers
    with modules, variables, outputs, and best practices.
    """
    
    def __init__(self):
        """Initialize Terraform Generator"""
        self.configs: Dict[str, TerraformConfig] = {}
    
    def create_config(
        self,
        project_name: str,
        cloud_provider: CloudProvider,
        region: str,
        environment: str = "production"
    ) -> TerraformConfig:
        """Create Terraform configuration"""
        config_id = f"tf_{uuid.uuid4().hex[:8]}"
        config = TerraformConfig(
            config_id=config_id,
            project_name=project_name,
            cloud_provider=cloud_provider,
            region=region,
            environment=environment,
            tags={"Project": project_name, "Environment": environment}
        )
        self.configs[config_id] = config
        return config
    
    def get_provider_block(self, config_id: str) -> str:
        """Get Terraform provider block"""
        if config_id not in self.configs:
            return ""
        config = self.configs[config_id]
        
        if config.cloud_provider == CloudProvider.AWS:
            return f"""terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
  
  backend "s3" {{
    bucket         = "{config.project_name}-tfstate"
    key            = "terraform/state"
    region         = "{config.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }}
}}

provider "aws" {{
  region = "{config.region}"
  
  default_tags {{
    tags = {{
      Project     = "{config.project_name}"
      Environment = "{config.environment}"
      ManagedBy   = "Terraform"
    }}
  }}
}}
"""
        elif config.cloud_provider == CloudProvider.AZURE:
            return f"""terraform {{
  required_version = ">= 1.0"
  required_providers {{
    azurerm = {{
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }}
  }}
  
  backend "azurerm" {{
    resource_group_name  = "{config.project_name}-state"
    storage_account_name = "{config.project_name.lower()}tfstate"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
  }}
}}

provider "azurerm" {{
  features {{
    virtual_machine {{
      graceful_shutdown = true
    }}
  }}
  
  subscription_id = var.subscription_id
}}
"""
        else:  # GCP
            return f"""terraform {{
  required_version = ">= 1.0"
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 5.0"
    }}
  }}
  
  backend "gcs" {{
    bucket = "{config.project_name}-tfstate"
    prefix = "terraform"
  }}
}}

provider "google" {{
  project = var.project_id
  region  = "{config.region}"
}}
"""
    
    def get_variables_file(self, config_id: str) -> str:
        """Get Terraform variables file"""
        if config_id not in self.configs:
            return ""
        config = self.configs[config_id]
        
        variables = """variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "region" {
  description = "Cloud region"
  type        = string
}

"""
        
        if config.cloud_provider == CloudProvider.AWS:
            variables += """variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "desired_capacity" {
  description = "Desired number of instances"
  type        = number
  default     = 3
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring"
  type        = bool
  default     = true
}
"""
        elif config.cloud_provider == CloudProvider.AZURE:
            variables += """variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  sensitive   = true
}

variable "admin_username" {
  description = "Admin username for VMs"
  type        = string
  default     = "azureuser"
}

variable "vm_size" {
  description = "VM size"
  type        = string
  default     = "Standard_B2s"
}
"""
        else:  # GCP
            variables += """variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "machine_type" {
  description = "GCE machine type"
  type        = string
  default     = "e2-medium"
}

variable "disk_size_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 20
}
"""
        
        return variables
    
    def get_networking_aws(self, config_id: str) -> str:
        """Get AWS networking resources"""
        if config_id not in self.configs:
            return ""
        config = self.configs[config_id]
        
        return f"""# VPC
resource "aws_vpc" "main" {{
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {{
    Name = "${{var.project_name}}-vpc"
  }}
}}

# Internet Gateway
resource "aws_internet_gateway" "main" {{
  vpc_id = aws_vpc.main.id
  
  tags = {{
    Name = "${{var.project_name}}-igw"
  }}
}}

# Public Subnets
resource "aws_subnet" "public" {{
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${{count.index + 1}}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {{
    Name = "${{var.project_name}}-public-subnet-${{count.index + 1}}"
  }}
}}

# Private Subnets
resource "aws_subnet" "private" {{
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${{count.index + 10}}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {{
    Name = "${{var.project_name}}-private-subnet-${{count.index + 1}}"
  }}
}}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {{
  count  = 2
  domain = "vpc"
  
  tags = {{
    Name = "${{var.project_name}}-eip-${{count.index + 1}}"
  }}
  
  depends_on = [aws_internet_gateway.main]
}}

# NAT Gateways
resource "aws_nat_gateway" "main" {{
  count         = 2
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  tags = {{
    Name = "${{var.project_name}}-nat-${{count.index + 1}}"
  }}
  
  depends_on = [aws_internet_gateway.main]
}}

# Public Route Table
resource "aws_route_table" "public" {{
  vpc_id = aws_vpc.main.id
  
  route {{
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }}
  
  tags = {{
    Name = "${{var.project_name}}-public-rt"
  }}
}}

# Public Route Table Associations
resource "aws_route_table_association" "public" {{
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}}

# Private Route Tables
resource "aws_route_table" "private" {{
  count  = 2
  vpc_id = aws_vpc.main.id
  
  route {{
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }}
  
  tags = {{
    Name = "${{var.project_name}}-private-rt-${{count.index + 1}}"
  }}
}}

# Private Route Table Associations
resource "aws_route_table_association" "private" {{
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}}

# Data source for AZs
data "aws_availability_zones" "available" {{
  state = "available"
}}
"""
    
    def get_compute_aws(self, config_id: str) -> str:
        """Get AWS compute resources"""
        if config_id not in self.configs:
            return ""
        config = self.configs[config_id]
        
        return """# Auto Scaling Group
resource "aws_launch_template" "main" {
  name_prefix   = "${var.project_name}-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  
  vpc_security_group_ids = [aws_security_group.app.id]
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-instance"
    }
  }
}

resource "aws_autoscaling_group" "main" {
  name                = "${var.project_name}-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  target_group_arns   = [aws_lb_target_group.main.arn]
  
  min_size         = var.min_capacity
  max_size         = var.max_capacity
  desired_capacity = var.desired_capacity
  
  launch_template {
    id      = aws_launch_template.main.id
    version = "$Latest"
  }
  
  tag {
    key                 = "Name"
    value               = "${var.project_name}-asg-instance"
    propagate_at_launch = true
  }
}

# ALB
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "main" {
  name        = "${var.project_name}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }
}

resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

# Security Groups
resource "aws_security_group" "alb" {
  name   = "${var.project_name}-alb-sg"
  vpc_id = aws_vpc.main.id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "app" {
  name   = "${var.project_name}-app-sg"
  vpc_id = aws_vpc.main.id
  
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Data source for Ubuntu AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}
"""
    
    def get_outputs_file(self, config_id: str) -> str:
        """Get Terraform outputs file"""
        if config_id not in self.configs:
            return ""
        config = self.configs[config_id]
        
        if config.cloud_provider == CloudProvider.AWS:
            return """output "vpc_id" {
  value       = aws_vpc.main.id
  description = "VPC ID"
}

output "alb_dns" {
  value       = aws_lb.main.dns_name
  description = "ALB DNS name"
}

output "alb_arn" {
  value       = aws_lb.main.arn
  description = "ALB ARN"
}

output "asg_name" {
  value       = aws_autoscaling_group.main.name
  description = "Auto Scaling Group name"
}
"""
        return ""
    
    def get_complete_main_tf(self, config_id: str) -> str:
        """Get complete main.tf file"""
        main_tf = self.get_provider_block(config_id)
        main_tf += "\n\n" + self.get_networking_aws(config_id)
        main_tf += "\n\n" + self.get_compute_aws(config_id)
        return main_tf
    
    def get_terraform_module_structure(self, config_id: str) -> str:
        """Get modular Terraform structure"""
        if config_id not in self.configs:
            return ""
        config = self.configs[config_id]
        
        structure = """# Terraform Module Structure

## Directory Layout
.
├── main.tf                 # Provider & root resources
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── terraform.tfvars        # Variable values
├── .terraform.lock.hcl     # Dependency lock file
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── vpc.tf
│   ├── compute/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── asg.tf
│   │   └── security_groups.tf
│   ├── database/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── rds.tf
│   └── monitoring/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── dev/
│   │   └── terraform.tfvars
│   ├── staging/
│   │   └── terraform.tfvars
│   └── production/
│       └── terraform.tfvars
└── docs/
    ├── architecture.md
    ├── deployment.md
    └── troubleshooting.md

## Module Usage Example

module "networking" {
  source = "./modules/networking"
  
  project_name = var.project_name
  vpc_cidr     = var.vpc_cidr
  region       = var.region
}

module "compute" {
  source = "./modules/compute"
  
  project_name     = var.project_name
  vpc_id           = module.networking.vpc_id
  subnet_ids       = module.networking.private_subnet_ids
  instance_type    = var.instance_type
  desired_capacity = var.desired_capacity
}
"""
        return structure


# Singleton instance
_terraform_generator = None

def get_terraform_generator() -> TerraformGenerator:
    """Get Terraform Generator singleton"""
    global _terraform_generator
    if _terraform_generator is None:
        _terraform_generator = TerraformGenerator()
    return _terraform_generator
