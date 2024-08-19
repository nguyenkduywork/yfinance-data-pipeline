variable "region" {
  description = "region to use for AWS resources"
  type        = string
  default     = "eu-west-1"
}

variable "global_prefix" {
  type    = string
  default = "demo-streaming"
}

variable "private_cidr_blocks" {
  type        = list(string)
  description = "Private Subnet CIDR values"
  default = [
    "10.0.1.0/24",
    "10.0.2.0/24",
    "10.0.3.0/24",
  ]
}

variable "public_cidr_blocks" {
  type        = list(string)
  description = "Public Subnet CIDR values"
  default = [
    "10.0.1.0/24",
    "10.0.2.0/24",
    "10.0.3.0/24",
  ]
}