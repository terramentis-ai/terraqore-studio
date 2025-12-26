"""
CloudFormationGenerator - AWS CloudFormation Template Generation

Generates CloudFormation JSON/YAML templates for AWS infrastructure deployment
with full resource management, parameters, outputs, and best practices.
"""

import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class ResourceType(Enum):
    """CloudFormation resource types"""
    VPC = "AWS::EC2::VPC"
    SUBNET = "AWS::EC2::Subnet"
    IGW = "AWS::EC2::InternetGateway"
    NAT_GATEWAY = "AWS::EC2::NatGateway"
    ROUTE_TABLE = "AWS::EC2::RouteTable"
    SECURITY_GROUP = "AWS::EC2::SecurityGroup"
    EC2_INSTANCE = "AWS::EC2::Instance"
    LAUNCH_TEMPLATE = "AWS::EC2::LaunchTemplate"
    ASG = "AWS::AutoScaling::AutoScalingGroup"
    ALB = "AWS::ElasticLoadBalancingV2::LoadBalancer"
    TARGET_GROUP = "AWS::ElasticLoadBalancingV2::TargetGroup"
    RDS_INSTANCE = "AWS::RDS::DBInstance"
    S3_BUCKET = "AWS::S3::Bucket"
    LAMBDA = "AWS::Lambda::Function"
    IAM_ROLE = "AWS::IAM::Role"
    CLOUDWATCH_LOG_GROUP = "AWS::Logs::LogGroup"
    SNS_TOPIC = "AWS::SNS::Topic"


@dataclass
class Parameter:
    """CloudFormation parameter"""
    name: str
    description: str
    param_type: str = "String"
    default: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None


@dataclass
class CFConfig:
    """CloudFormation configuration"""
    config_id: str
    stack_name: str
    region: str = "us-east-1"
    environment: str = "production"
    parameters: List[Parameter] = field(default_factory=list)
    resources: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    outputs: Dict[str, Dict[str, str]] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CloudFormationGenerator:
    """
    CloudFormation Template Generator
    
    Generates CloudFormation templates for AWS infrastructure deployment
    with proper structure, parameters, outputs, and best practices.
    """
    
    def __init__(self):
        """Initialize CloudFormation Generator"""
        self.configs: Dict[str, CFConfig] = {}
    
    def create_config(
        self,
        stack_name: str,
        region: str = "us-east-1",
        environment: str = "production"
    ) -> CFConfig:
        """Create CloudFormation configuration"""
        config_id = f"cf_{uuid.uuid4().hex[:8]}"
        config = CFConfig(
            config_id=config_id,
            stack_name=stack_name,
            region=region,
            environment=environment
        )
        self.configs[config_id] = config
        return config
    
    def get_template_vpc(self, config_id: str) -> Dict[str, Any]:
        """Get VPC CloudFormation template"""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "VPC Stack",
            "Parameters": {
                "VpcCidr": {
                    "Type": "String",
                    "Default": "10.0.0.0/16",
                    "Description": "VPC CIDR block"
                },
                "Environment": {
                    "Type": "String",
                    "Default": "production",
                    "AllowedValues": ["development", "staging", "production"]
                }
            },
            "Resources": {
                "VPC": {
                    "Type": "AWS::EC2::VPC",
                    "Properties": {
                        "CidrBlock": {"Ref": "VpcCidr"},
                        "EnableDnsHostnames": True,
                        "EnableDnsSupport": True,
                        "Tags": [
                            {"Key": "Name", "Value": {"Ref": "AWS::StackName"}},
                            {"Key": "Environment", "Value": {"Ref": "Environment"}}
                        ]
                    }
                },
                "InternetGateway": {
                    "Type": "AWS::EC2::InternetGateway",
                    "Properties": {
                        "Tags": [
                            {"Key": "Name", "Value": f"{{{{'Ref': 'AWS::StackName'}}}}-igw"}
                        ]
                    }
                },
                "AttachGateway": {
                    "Type": "AWS::EC2::VPCGatewayAttachment",
                    "Properties": {
                        "VpcId": {"Ref": "VPC"},
                        "InternetGatewayId": {"Ref": "InternetGateway"}
                    }
                },
                "PublicSubnet1": {
                    "Type": "AWS::EC2::Subnet",
                    "Properties": {
                        "VpcId": {"Ref": "VPC"},
                        "CidrBlock": "10.0.1.0/24",
                        "AvailabilityZone": {"Fn::Select": [0, {"Fn::GetAZs": ""}]},
                        "MapPublicIpOnLaunch": True,
                        "Tags": [{"Key": "Name", "Value": f"{{{{'Ref': 'AWS::StackName'}}}}-public-1"}]
                    }
                },
                "PublicSubnet2": {
                    "Type": "AWS::EC2::Subnet",
                    "Properties": {
                        "VpcId": {"Ref": "VPC"},
                        "CidrBlock": "10.0.2.0/24",
                        "AvailabilityZone": {"Fn::Select": [1, {"Fn::GetAZs": ""}]},
                        "MapPublicIpOnLaunch": True,
                        "Tags": [{"Key": "Name", "Value": f"{{{{'Ref': 'AWS::StackName'}}}}-public-2"}]
                    }
                },
                "PrivateSubnet1": {
                    "Type": "AWS::EC2::Subnet",
                    "Properties": {
                        "VpcId": {"Ref": "VPC"},
                        "CidrBlock": "10.0.10.0/24",
                        "AvailabilityZone": {"Fn::Select": [0, {"Fn::GetAZs": ""}]},
                        "Tags": [{"Key": "Name", "Value": f"{{{{'Ref': 'AWS::StackName'}}}}-private-1"}]
                    }
                },
                "PrivateSubnet2": {
                    "Type": "AWS::EC2::Subnet",
                    "Properties": {
                        "VpcId": {"Ref": "VPC"},
                        "CidrBlock": "10.0.11.0/24",
                        "AvailabilityZone": {"Fn::Select": [1, {"Fn::GetAZs": ""}]},
                        "Tags": [{"Key": "Name", "Value": f"{{{{'Ref': 'AWS::StackName'}}}}-private-2"}]
                    }
                },
                "PublicRouteTable": {
                    "Type": "AWS::EC2::RouteTable",
                    "Properties": {
                        "VpcId": {"Ref": "VPC"},
                        "Tags": [{"Key": "Name", "Value": f"{{{{'Ref': 'AWS::StackName'}}}}-public-rt"}]
                    }
                },
                "PublicRoute": {
                    "Type": "AWS::EC2::Route",
                    "DependsOn": "AttachGateway",
                    "Properties": {
                        "RouteTableId": {"Ref": "PublicRouteTable"},
                        "DestinationCidrBlock": "0.0.0.0/0",
                        "GatewayId": {"Ref": "InternetGateway"}
                    }
                },
                "PublicSubnet1RouteTableAssociation": {
                    "Type": "AWS::EC2::SubnetRouteTableAssociation",
                    "Properties": {
                        "SubnetId": {"Ref": "PublicSubnet1"},
                        "RouteTableId": {"Ref": "PublicRouteTable"}
                    }
                },
                "PublicSubnet2RouteTableAssociation": {
                    "Type": "AWS::EC2::SubnetRouteTableAssociation",
                    "Properties": {
                        "SubnetId": {"Ref": "PublicSubnet2"},
                        "RouteTableId": {"Ref": "PublicRouteTable"}
                    }
                }
            },
            "Outputs": {
                "VpcId": {
                    "Description": "VPC ID",
                    "Value": {"Ref": "VPC"},
                    "Export": {"Name": f"{{{{'Ref': 'AWS::StackName'}}}}-VPC-ID"}
                },
                "PublicSubnet1": {
                    "Description": "Public Subnet 1",
                    "Value": {"Ref": "PublicSubnet1"},
                    "Export": {"Name": f"{{{{'Ref': 'AWS::StackName'}}}}-Public-Subnet-1"}
                },
                "PublicSubnet2": {
                    "Description": "Public Subnet 2",
                    "Value": {"Ref": "PublicSubnet2"},
                    "Export": {"Name": f"{{{{'Ref': 'AWS::StackName'}}}}-Public-Subnet-2"}
                },
                "PrivateSubnet1": {
                    "Description": "Private Subnet 1",
                    "Value": {"Ref": "PrivateSubnet1"},
                    "Export": {"Name": f"{{{{'Ref': 'AWS::StackName'}}}}-Private-Subnet-1"}
                },
                "PrivateSubnet2": {
                    "Description": "Private Subnet 2",
                    "Value": {"Ref": "PrivateSubnet2"},
                    "Export": {"Name": f"{{{{'Ref': 'AWS::StackName'}}}}-Private-Subnet-2"}
                }
            }
        }
        return template
    
    def get_template_alb(self) -> Dict[str, Any]:
        """Get ALB CloudFormation template"""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Application Load Balancer Stack",
            "Parameters": {
                "VpcId": {
                    "Type": "AWS::EC2::VPC::Id",
                    "Description": "VPC ID"
                },
                "SubnetIds": {
                    "Type": "List<AWS::EC2::Subnet::Id>",
                    "Description": "Subnet IDs for ALB"
                }
            },
            "Resources": {
                "ALBSecurityGroup": {
                    "Type": "AWS::EC2::SecurityGroup",
                    "Properties": {
                        "GroupDescription": "ALB Security Group",
                        "VpcId": {"Ref": "VpcId"},
                        "SecurityGroupIngress": [
                            {
                                "IpProtocol": "tcp",
                                "FromPort": 80,
                                "ToPort": 80,
                                "CidrIp": "0.0.0.0/0"
                            },
                            {
                                "IpProtocol": "tcp",
                                "FromPort": 443,
                                "ToPort": 443,
                                "CidrIp": "0.0.0.0/0"
                            }
                        ],
                        "Tags": [{"Key": "Name", "Value": "alb-sg"}]
                    }
                },
                "ApplicationLoadBalancer": {
                    "Type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
                    "Properties": {
                        "Name": "app-alb",
                        "Type": "application",
                        "Scheme": "internet-facing",
                        "IpAddressType": "ipv4",
                        "Subnets": {"Ref": "SubnetIds"},
                        "SecurityGroups": [{"Ref": "ALBSecurityGroup"}],
                        "Tags": [{"Key": "Name", "Value": "app-alb"}]
                    }
                },
                "TargetGroup": {
                    "Type": "AWS::ElasticLoadBalancingV2::TargetGroup",
                    "Properties": {
                        "Name": "app-tg",
                        "Port": 8000,
                        "Protocol": "HTTP",
                        "VpcId": {"Ref": "VpcId"},
                        "HealthCheckEnabled": True,
                        "HealthCheckProtocol": "HTTP",
                        "HealthCheckPath": "/health",
                        "HealthCheckIntervalSeconds": 30,
                        "HealthCheckTimeoutSeconds": 5,
                        "HealthyThresholdCount": 2,
                        "UnhealthyThresholdCount": 3,
                        "TargetType": "instance"
                    }
                },
                "Listener": {
                    "Type": "AWS::ElasticLoadBalancingV2::Listener",
                    "Properties": {
                        "LoadBalancerArn": {"Ref": "ApplicationLoadBalancer"},
                        "Port": 80,
                        "Protocol": "HTTP",
                        "DefaultActions": [
                            {
                                "Type": "forward",
                                "TargetGroupArn": {"Ref": "TargetGroup"}
                            }
                        ]
                    }
                }
            },
            "Outputs": {
                "ALBArn": {
                    "Description": "ALB ARN",
                    "Value": {"Ref": "ApplicationLoadBalancer"}
                },
                "ALBDnsName": {
                    "Description": "ALB DNS Name",
                    "Value": {"Fn::GetAtt": ["ApplicationLoadBalancer", "DNSName"]}
                },
                "TargetGroupArn": {
                    "Description": "Target Group ARN",
                    "Value": {"Ref": "TargetGroup"}
                }
            }
        }
        return template
    
    def get_template_rds(self) -> Dict[str, Any]:
        """Get RDS CloudFormation template"""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "RDS Database Stack",
            "Parameters": {
                "DBName": {
                    "Type": "String",
                    "Default": "appdb",
                    "Description": "Database name"
                },
                "DBUsername": {
                    "Type": "String",
                    "NoEcho": True,
                    "Description": "Database master username"
                },
                "DBPassword": {
                    "Type": "String",
                    "NoEcho": True,
                    "Description": "Database master password"
                },
                "DBInstanceClass": {
                    "Type": "String",
                    "Default": "db.t3.medium",
                    "Description": "Database instance class"
                }
            },
            "Resources": {
                "DBSubnetGroup": {
                    "Type": "AWS::RDS::DBSubnetGroup",
                    "Properties": {
                        "DBSubnetGroupDescription": "Subnet group for RDS",
                        "SubnetIds": [
                            {"Ref": "PrivateSubnet1"},
                            {"Ref": "PrivateSubnet2"}
                        ],
                        "Tags": [{"Key": "Name", "Value": "db-subnet-group"}]
                    }
                },
                "DBSecurityGroup": {
                    "Type": "AWS::EC2::SecurityGroup",
                    "Properties": {
                        "GroupDescription": "RDS Security Group",
                        "VpcId": {"Ref": "VpcId"},
                        "SecurityGroupIngress": [
                            {
                                "IpProtocol": "tcp",
                                "FromPort": 5432,
                                "ToPort": 5432,
                                "CidrIp": "10.0.0.0/16"
                            }
                        ]
                    }
                },
                "Database": {
                    "Type": "AWS::RDS::DBInstance",
                    "Properties": {
                        "DBInstanceIdentifier": "app-database",
                        "DBInstanceClass": {"Ref": "DBInstanceClass"},
                        "Engine": "postgres",
                        "EngineVersion": "15.2",
                        "MasterUsername": {"Ref": "DBUsername"},
                        "MasterUserPassword": {"Ref": "DBPassword"},
                        "DBName": {"Ref": "DBName"},
                        "AllocatedStorage": "20",
                        "StorageType": "gp3",
                        "StorageEncrypted": True,
                        "MultiAZ": True,
                        "DBSubnetGroupName": {"Ref": "DBSubnetGroup"},
                        "VPCSecurityGroups": [{"Ref": "DBSecurityGroup"}],
                        "BackupRetentionPeriod": 30,
                        "PreferredBackupWindow": "03:00-04:00",
                        "PreferredMaintenanceWindow": "sun:04:00-sun:05:00",
                        "EnableCloudwatchLogsExports": ["postgresql"],
                        "EnableIAMDatabaseAuthentication": True,
                        "Tags": [{"Key": "Name", "Value": "app-database"}]
                    }
                }
            },
            "Outputs": {
                "DatabaseEndpoint": {
                    "Description": "Database endpoint",
                    "Value": {"Fn::GetAtt": ["Database", "Endpoint.Address"]}
                },
                "DatabasePort": {
                    "Description": "Database port",
                    "Value": {"Fn::GetAtt": ["Database", "Endpoint.Port"]}
                }
            }
        }
        return template
    
    def get_yaml_template(self, template_dict: Dict[str, Any]) -> str:
        """Convert template to YAML format"""
        import yaml
        return yaml.dump(template_dict, default_flow_style=False, sort_keys=False)
    
    def get_json_template(self, template_dict: Dict[str, Any]) -> str:
        """Convert template to JSON format"""
        return json.dumps(template_dict, indent=2)


# Singleton instance
_cloudformation_generator = None

def get_cloudformation_generator() -> CloudFormationGenerator:
    """Get CloudFormation Generator singleton"""
    global _cloudformation_generator
    if _cloudformation_generator is None:
        _cloudformation_generator = CloudFormationGenerator()
    return _cloudformation_generator
