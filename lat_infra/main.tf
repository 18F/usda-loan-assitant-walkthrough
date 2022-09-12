
######################################
#############security_group###########
######################################
resource "aws_security_group" "alb" {
  name        = "alb_security_group"
  description = "load balancer security group"
  vpc_id      = "${var.vpc-id}"


   dynamic "ingress"  {
      iterator =  port
      for_each = var.ingressrules
      content {
      from_port = port.value
      to_port =  port.value
      protocol = "TCP"
      cidr_blocks = ["0.0.0.0/0"]
      }

              }

  # Allow all outbound traffic.
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

   tags = {
        Name = "ALB&EC2"
    
    
    }
 }

 #################################
 #############ACM#################
 #################################
 resource "tls_private_key" "alb" {
  algorithm = "RSA"
}

resource "tls_self_signed_cert" "albcert" {
 # name = "USDA-LAT-Infra-ACM"
  private_key_pem = tls_private_key.alb.private_key_pem

   subject {
    common_name  = "USDA-LAT-Infra.ACM"
    organization = "ACME terraform ex, Inc"
  }


  validity_period_hours = 12

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
  ]

}

resource "aws_acm_certificate" "cert" {
  private_key      = tls_private_key.alb.private_key_pem
  certificate_body = tls_self_signed_cert.albcert.cert_pem
}

####################################
##############SNS###################
####################################
resource "aws_sns_topic" "user_updates" {
  name            = "USDA-LAT-Infra-SNS-Topic"
  delivery_policy = <<EOF
{
  "http": {
    "defaultHealthyRetryPolicy": {
      "minDelayTarget": 20,
      "maxDelayTarget": 20,
      "numRetries": 3,
      "numMaxDelayRetries": 0,
      "numNoDelayRetries": 0,
      "numMinDelayRetries": 0,
      "backoffFunction": "linear"
    },
    "disableSubscriptionOverrides": false,
    "defaultThrottlePolicy": {
      "maxReceivesPerSecond": 1
    }
  }
}
EOF
}

resource "aws_sns_topic_subscription" "email-target" {
  topic_arn = aws_sns_topic.user_updates.arn
  protocol  = "email"
  endpoint  = var.email-id
}
resource "aws_sns_topic_policy" "ASG" {
  arn = aws_sns_topic.user_updates.arn

  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

data "aws_iam_policy_document" "sns_topic_policy" {
  policy_id = "ASG-SNS-Policy"

  statement {
    actions = [
      "SNS:Subscribe",
      "SNS:SetTopicAttributes",
      "SNS:RemovePermission",
      "SNS:Receive",
      "SNS:Publish",
      "SNS:ListSubscriptionsByTopic",
      "SNS:GetTopicAttributes",
      "SNS:DeleteTopic",
      "SNS:AddPermission",
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceOwner"

      values = [
        var.account-id,
      ]
    }

    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    resources = [
      aws_sns_topic.user_updates.arn,
    ]

    sid = "ASG-SNS-Policy"
  }
}

######################################
#############ALB######################
######################################

resource "aws_lb" "webasglb" {
  name               = "USDA-LAT-Infra-ALB"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
 # subnets            = [var.subnet1,var.subnet2]
subnets = var.subnets-ids
 

  tags = {
    Environment = "USDA-LAT-Infra-Application-Load-Balancer"
  }
}

resource "aws_alb_target_group" "group" {
  name     = "USDA-LAT-Infra-Target-Group"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc-id
 
  stickiness {
    type = "lb_cookie"
  }
  
  # Alter the destination of the health check to be the login page.
  health_check {
    path = "/"
    port = 80
  }
}

resource "aws_alb_listener" "listener_http" {
  load_balancer_arn = "${aws_lb.webasglb.arn}"
  port              = "80"
  protocol          = "HTTP"

  default_action {
    target_group_arn = "${aws_alb_target_group.group.arn}"
    type             = "forward"
  }
}

resource "aws_lb_listener" "listener_https" {
  load_balancer_arn = aws_lb.webasglb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate.cert.arn

  default_action {
    type             = "forward"
    target_group_arn = "${aws_alb_target_group.group.arn}"
  }
}

resource "aws_lb_listener_rule" "redirect_http_to_https" {
  listener_arn = aws_alb_listener.listener_http.arn

  action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
  condition {
    source_ip {
       values           = ["0.0.0.0/0"]
    }
  }
}

################################
##########ASG###################
################################

resource "aws_launch_configuration" "asg_conf" {
  name   = "USDA-LAT-Infra- Launch-Configuration"
  image_id      = var.image-id
  instance_type = var.instance-type
  key_name = var.key-name
   security_groups = [ aws_security_group.alb.id ]
  associate_public_ip_address = true
  root_block_device {
    volume_size = "${var.root_volume_size}"
    volume_type = "${var.root_volume_type}"
 
}

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "web" {
  name = "USDA-LAT-Infra-Auto-Scaling-Group"

  min_size             = 2
  desired_capacity     = 2
  max_size             = 4
  
  health_check_type    = "ELB"
 target_group_arns = [aws_alb_target_group.group.arn]

  launch_configuration = aws_launch_configuration.asg_conf.name

  enabled_metrics = [
    "GroupMinSize",
    "GroupMaxSize",
    "GroupDesiredCapacity",
    "GroupInServiceInstances",
    "GroupTotalInstances"
  ]

  metrics_granularity = "1Minute"

  vpc_zone_identifier  = var.subnets-ids

  # Required to redeploy without an outage.
  lifecycle {
    create_before_destroy = true
  }

  tag {
    key                 = "Name"
    value               = "USDA-LAT-Infra-Ec2-Instance"
    propagate_at_launch = true
  }

}

resource "aws_autoscaling_policy" "web_policy_up" {
  name = "USDA-LAT-Infra-CloudWatch-up"
  scaling_adjustment = 1
  adjustment_type = "ChangeInCapacity"
  cooldown = 60
  autoscaling_group_name = aws_autoscaling_group.web.name
}

resource "aws_cloudwatch_metric_alarm" "web_cpu_alarm_up" {
  alarm_name = "USDA-LAT-Infra-CloudWatch-up"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods = "2"
  metric_name = "CPUUtilization"
  namespace = "AWS/EC2"
  period = "60"
  statistic = "Average"
  threshold = "75"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.web.name
  }

  alarm_description = "This metric monitor EC2 instance CPU utilization"
  alarm_actions = [ aws_autoscaling_policy.web_policy_up.arn ]
}

resource "aws_autoscaling_policy" "web_policy_down" {
  name = "USDA-LAT-Infra-CloudWatch-down"
  scaling_adjustment = -1
  adjustment_type = "ChangeInCapacity"
  cooldown = 60
  autoscaling_group_name = aws_autoscaling_group.web.name
}

resource "aws_cloudwatch_metric_alarm" "web_cpu_alarm_down" {
  alarm_name = "USDA-LAT-Infra-CloudWatch-down"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods = "2"
  metric_name = "CPUUtilization"
  namespace = "AWS/EC2"
  period = "60"
  statistic = "Average"
  threshold = "40"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.web.name
  }

  alarm_description = "This metric monitor EC2 instance CPU utilization"
  alarm_actions = [ aws_autoscaling_policy.web_policy_down.arn ]
}

resource "aws_autoscaling_notification" "sns_notifications" {
  group_names = [
    aws_autoscaling_group.web.name
  ]

  notifications = [
    "autoscaling:EC2_INSTANCE_LAUNCH",
    "autoscaling:EC2_INSTANCE_TERMINATE",
    "autoscaling:EC2_INSTANCE_LAUNCH_ERROR",
    "autoscaling:EC2_INSTANCE_TERMINATE_ERROR",
  ]

  topic_arn = aws_sns_topic.user_updates.arn
}

############################################
#################Cloudwatch Dashboard#######
############################################
resource "aws_cloudwatch_dashboard" "ec2" {
  dashboard_name = "USDA-LAT-Infra-CloudWatch-Dashboard"

  dashboard_body = <<EOF
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/EC2","CPUUtilization","AutoScalingGroupName","${aws_autoscaling_group.web.name}"],
            ["AWS/EC2","NetworkPacketsIn","AutoScalingGroupName","${aws_autoscaling_group.web.name}"],
            ["AWS/EC2","NetworkPacketsOut","AutoScalingGroupName","${aws_autoscaling_group.web.name}"],
            ["AWS/EC2","NetworkIn","AutoScalingGroupName","${aws_autoscaling_group.web.name}"],
            ["AWS/EC2","NetworkOut","AutoScalingGroupName","${aws_autoscaling_group.web.name}"],
            ["AWS/EC2","DiskReadOps","AutoScalingGroupName","${aws_autoscaling_group.web.name}"],
            ["AWS/EC2","DiskWriteOps","AutoScalingGroupName","${aws_autoscaling_group.web.name}"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "${var.region}",
        "title": "EC2 Instance CPU"
      }
    },
    {
      "type": "text",
      "x": 0,
      "y": 7,
      "width": 3,
      "height": 3,
      "properties": {
        "markdown": "Hello world"
      }
    }
  ]
}
EOF
}