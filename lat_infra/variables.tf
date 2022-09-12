variable "region" {
    description = "Provide AWS region in which you want to create infra"
    type = string
}

variable "vpc-id" {
  type = string
description = "Provide VPC ID for autoscalling group"

}

variable "allowcidr_blocks" {
  type = string
  default = "0.0.0.0/0"

}
variable "subnets-ids" {
  description = "A list of subnets to associate with the load balancer. e.g. ['subnet-1a2b3c4d','subnet-1a2b3c4e','subnet-1a2b3c4f']"
  type        = list(string)
}

variable "image-id" {
  type = string
  description = "provide Image id in which should have 80 number port open or web server is on runing  state "
}

variable "instance-type" {
  type = string
  default = "t2.micro"

}

variable "root_volume_size" {
  type = number
  default = "30"
}
variable "root_volume_type" {
  type = string
  default = "gp2"
}

variable "account-id" {
  description = "Provide the AWS account ID"
  type = number
 
}
variable "email-id" {
  description = "Provide the Email account id for notification"
  type = string
 
}



variable "ingressrules" {
    type = list(number)
    default = [ 80,443,22 ]
}
variable "key-name" {
    type = string
  description = "provide Key-name for ec2"
}