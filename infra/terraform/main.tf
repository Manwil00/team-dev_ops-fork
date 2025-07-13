provider "aws" {
  region                  = "us-east-1"
  shared_credentials_files = ["~/.aws/credentials"]
}

# Reference an existing EC2 instance
data "aws_instance" "existing_instance" {
  instance_id = "<your_instance_id>"  # Replace with your actual instance ID
}

# Retrieve the subnet details to get the VPC ID
data "aws_subnet" "instance_subnet" {
  id = data.aws_instance.existing_instance.subnet_id
}

#Conditional Logic for Security Group:

# Check if a security group with that name already exists.
data "aws_security_groups" "existing_sg_lookup" {
  filter {
    name   = "vpc-id"
    values = [data.aws_subnet.instance_subnet.vpc_id]
  }
  filter {
    name   = "group-name"
    values = ["app-security-group"]
  }
}

# Create the security group only if the lookup above found nothing.
#    The 'count' trick means: if the list of IDs is empty (length is 0), create 1 of these. Otherwise, create 0.
resource "aws_security_group" "app_sg_created" {
  count       = length(data.aws_security_groups.existing_sg_lookup.ids) == 0 ? 1 : 0
  name        = "app-security-group"
  description = "Security group for application"
  vpc_id      = data.aws_subnet.instance_subnet.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["<ip-address>/32"] # Replace with your public IP
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "app-security-group"
  }
}

# Create a local variable to hold the correct security group ID.
locals {
  app_sg_id = length(data.aws_security_groups.existing_sg_lookup.ids) == 0 ? aws_security_group.app_sg_created[0].id : data.aws_security_groups.existing_sg_lookup.ids[0]
}


# Attach the security group to the instance's network interface
resource "aws_network_interface_sg_attachment" "sg_attachment" {
  security_group_id    = local.app_sg_id
  network_interface_id = data.aws_instance.existing_instance.network_interface_id
}