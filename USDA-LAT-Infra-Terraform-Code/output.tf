
output "ALB_DNS" {
    description = "ALB DNS value"
  value       = aws_lb.webasglb.dns_name
  
}