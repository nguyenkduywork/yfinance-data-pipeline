################################################################################
# Cluster
################################################################################
module "emr_serverless_spark" {
  source  = "terraform-aws-modules/emr/aws//modules/serverless"
  version = "1.1.2"

  name = "emr-serverless-spark-demo"

  release_label_prefix = "emr-6"

  initial_capacity = {
    driver = {
      initial_capacity_type = "Driver"

      initial_capacity_config = {
        worker_count = 2
        worker_configuration = {
          cpu    = "2 vCPU"
          memory = "10 GB"
        }
      }
    }

    executor = {
      initial_capacity_type = "Executor"

      initial_capacity_config = {
        worker_count = 2
        worker_configuration = {
          cpu    = "2 vCPU"
          disk   = "32 GB"
          memory = "10 GB"
        }
      }
    }
  }

  maximum_capacity = {
    cpu    = "12 vCPU"
    memory = "100 GB"
  }

  network_configuration = {
    subnet_ids = [aws_subnet.public_subnet[1].id, aws_subnet.public_subnet[2].id]
  }

  security_group_rules = {
    egress_all = {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
}

################################################################################
# Supporting Resources
################################################################################

resource "aws_s3_bucket" "demo" {
  bucket = "demo-bucket"
}

resource "aws_s3_object" "artifacts" {
  bucket = aws_s3_bucket.demo.id
  key    = "artifacts/"
}

resource "aws_s3_object" "code" {
  bucket = aws_s3_bucket.demo.id
  key    = "code/"
}

################################################################################
# MSK Cluster
################################################################################
resource "aws_kms_key" "kafka_kms_key" {
  description = "Key for Apache Kafka"
}

resource "aws_cloudwatch_log_group" "kafka_log_group" {
  name = "kafka_broker_logs"
}

resource "aws_msk_configuration" "kafka_config" {
  kafka_versions    = ["3.4.0"]
  name              = "${var.global_prefix}-config"
  server_properties = <<EOF
auto.create.topics.enable = true
delete.topic.enable = true
EOF
}

resource "aws_msk_cluster" "kafka" {
  cluster_name           = var.global_prefix
  kafka_version          = "3.4.0"
  number_of_broker_nodes = 3
  broker_node_group_info {
    instance_type = "kafka.m5.large"  # default value
    storage_info {
      ebs_storage_info {
        volume_size = 1000
      }
    }
    client_subnets = [aws_subnet.private_subnet[0].id,
      aws_subnet.private_subnet[1].id,
    aws_subnet.private_subnet[2].id]
    security_groups = [aws_security_group.kafka.id]
  }
  encryption_info {
    encryption_in_transit {
      client_broker = "PLAINTEXT"
    }
    encryption_at_rest_kms_key_arn = aws_kms_key.kafka_kms_key.arn
  }
  configuration_info {
    arn      = aws_msk_configuration.kafka_config.arn
    revision = aws_msk_configuration.kafka_config.latest_revision
  }
  open_monitoring {
    prometheus {
      jmx_exporter {
        enabled_in_broker = true
      }
      node_exporter {
        enabled_in_broker = true
      }
    }
  }
  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.kafka_log_group.name
      }
    }
  }
}

################################################################################
# General
################################################################################

resource "aws_vpc" "default" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
}

resource "aws_internet_gateway" "default" {
  vpc_id = aws_vpc.default.id
}

resource "aws_eip" "default" {
  depends_on = [aws_internet_gateway.default]
  domain     = "vpc"
}

resource "aws_route" "default" {
  route_table_id         = aws_vpc.default.main_route_table_id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.default.id
}

resource "aws_route_table" "second_route_table" {
  vpc_id = aws_vpc.default.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.default.id
  }
}

# Enable Internet traffic for the public subnet
resource "aws_route_table_association" "public_subnet_association" {
  count          = length(data.aws_availability_zones.available.names)
  subnet_id      = element(aws_subnet.public_subnet.*.id, count.index)
  route_table_id = aws_route_table.second_route_table.id
}

################################################################################
# Subnets
################################################################################

resource "aws_subnet" "private_subnet" {
  count                   = length(var.private_cidr_blocks)
  vpc_id                  = aws_vpc.default.id
  cidr_block              = element(var.private_cidr_blocks, count.index)
  map_public_ip_on_launch = false
  availability_zone       = data.aws_availability_zones.available.names[count.index]
}

resource "aws_subnet" "public_subnet" {
  count                   = length(var.public_cidr_blocks)
  vpc_id                  = aws_vpc.default.id
  cidr_block              = element(var.public_cidr_blocks, count.index)
  map_public_ip_on_launch = true
  availability_zone       = data.aws_availability_zones.available.names[count.index]
}

################################################################################
# Security groups
################################################################################

resource "aws_security_group" "kafka" {
  name   = "${var.global_prefix}-kafka"
  vpc_id = aws_vpc.default.id
  ingress {
    from_port = 0
    to_port   = 9092
    protocol  = "TCP"
    cidr_blocks = ["10.0.1.0/24",
      "10.0.2.0/24",
    "10.0.3.0/24"]
  }
  ingress {
    from_port   = 0
    to_port     = 9092
    protocol    = "TCP"
    cidr_blocks = ["10.0.4.0/24"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "bastion_host" {
  name   = "${var.global_prefix}-bastion-host"
  vpc_id = aws_vpc.default.id
  ingress {
    from_port   = 22
    to_port     = 22
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

resource "tls_private_key" "private_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "private_key" {
  key_name   = var.global_prefix
  public_key = tls_private_key.private_key.public_key_openssh
}

resource "local_file" "private_key" {
  content  = tls_private_key.private_key.private_key_pem
  filename = "cert.pem"
}

resource "null_resource" "private_key_permissions" {
  depends_on = [local_file.private_key]
  provisioner "local-exec" {
    command     = "chmod 600 cert.pem"
    interpreter = ["bash", "-c"]
    on_failure  = continue
  }
}

################################################################################
# Client Machine (EC2)
################################################################################

resource "aws_instance" "bastion_host" {
  depends_on             = [aws_msk_cluster.kafka]
  ami                    = data.aws_ami.amazon_linux_2024.id
  instance_type          = "t2.micro"
  key_name               = aws_key_pair.private_key.key_name
  subnet_id              = aws_subnet.public_subnet[0].id # aws_subnet.bastion_host_subnet.id
  vpc_security_group_ids = [aws_security_group.bastion_host.id]
  user_data = templatefile("bastion.tftpl", {
    bootstrap_server_1 = split(",", aws_msk_cluster.kafka.bootstrap_brokers)[0]
    bootstrap_server_2 = split(",", aws_msk_cluster.kafka.bootstrap_brokers)[1]
    bootstrap_server_3 = split(",", aws_msk_cluster.kafka.bootstrap_brokers)[2]
  })
  root_block_device {
    volume_type = "gp2"
    volume_size = 100
  }
}