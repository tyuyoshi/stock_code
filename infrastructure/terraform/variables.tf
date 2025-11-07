# Terraform Variables for Stock Code Infrastructure

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "asia-northeast1-a"
}

# Database variables
variable "db_user" {
  description = "Database user name"
  type        = string
  default     = "stockcode"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "stockcode"
}

# Application variables
variable "app_name" {
  description = "Application name"
  type        = string
  default     = "stock-code"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# Notification variables
variable "notification_emails" {
  description = "Comma-separated list of email addresses for notifications"
  type        = string
  default     = ""
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  default     = ""
  sensitive   = true
}

# Container image variables
variable "backend_image_tag" {
  description = "Backend container image tag"
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "Frontend container image tag"
  type        = string
  default     = "latest"
}

# Compute resources
variable "backend_cpu" {
  description = "CPU allocation for backend service"
  type        = string
  default     = "1000m"
}

variable "backend_memory" {
  description = "Memory allocation for backend service"
  type        = string
  default     = "2Gi"
}

variable "backend_min_instances" {
  description = "Minimum number of backend instances"
  type        = number
  default     = 0
}

variable "backend_max_instances" {
  description = "Maximum number of backend instances"
  type        = number
  default     = 10
}

# Database instance variables
variable "db_tier" {
  description = "Database instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_disk_size" {
  description = "Database disk size in GB"
  type        = number
  default     = 20
}

variable "db_backup_enabled" {
  description = "Enable database backups"
  type        = bool
  default     = true
}

# Redis variables
variable "redis_memory_size" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

variable "redis_tier" {
  description = "Redis service tier"
  type        = string
  default     = "BASIC"
}

# Security variables
variable "authorized_networks" {
  description = "List of authorized networks for database access"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "enable_ssl" {
  description = "Enable SSL for database connections"
  type        = bool
  default     = true
}

# Monitoring variables
variable "enable_monitoring" {
  description = "Enable Cloud Monitoring"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable Cloud Logging"
  type        = bool
  default     = true
}

# Domain and DNS variables
variable "domain_name" {
  description = "Custom domain name for the application"
  type        = string
  default     = ""
}

variable "ssl_certificate_domains" {
  description = "List of domains for SSL certificate"
  type        = list(string)
  default     = []
}