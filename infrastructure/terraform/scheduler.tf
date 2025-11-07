# Cloud Scheduler for Stock Code Batch Jobs

# Enable required APIs
resource "google_project_service" "scheduler_api" {
  service = "cloudscheduler.googleapis.com"
}

resource "google_project_service" "run_api" {
  service = "run.googleapis.com"
}

# Service Account for Cloud Scheduler
resource "google_service_account" "scheduler_sa" {
  account_id   = "stock-code-scheduler"
  display_name = "Stock Code Scheduler Service Account"
  description  = "Service account for running Stock Code batch jobs"
}

# IAM roles for the service account
resource "google_project_iam_member" "scheduler_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

resource "google_project_iam_member" "scheduler_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

# Cloud Run Job for Daily Stock Price Update
resource "google_cloud_run_v2_job" "daily_stock_update" {
  name     = "stock-code-daily-update"
  location = var.region

  template {
    template {
      service_account = google_service_account.scheduler_sa.email
      
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/stock-code/backend:latest"
        
        # Resources
        resources {
          limits = {
            cpu    = "1000m"
            memory = "2Gi"
          }
        }
        
        # Environment variables
        env {
          name  = "DATABASE_URL"
          value = "postgresql://${var.db_user}:${var.db_password}@${google_sql_database_instance.main.connection_name}/${var.db_name}"
        }
        
        env {
          name  = "REDIS_URL"
          value = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}/0"
        }
        
        env {
          name  = "ENVIRONMENT"
          value = "production"
        }
        
        env {
          name  = "SECRET_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.secret_key.secret_id
              version = "latest"
            }
          }
        }
        
        # Notification settings
        env {
          name  = "SLACK_WEBHOOK_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.slack_webhook.secret_id
              version = "latest"
            }
          }
        }
        
        env {
          name  = "EMAIL_NOTIFICATIONS_ENABLED"
          value = "true"
        }
        
        env {
          name  = "NOTIFICATION_EMAILS"
          value = var.notification_emails
        }
        
        # Command to run
        command = ["/bin/sh"]
        args = [
          "-c",
          "cd /app && python -m batch.daily_update"
        ]
      }
      
      # Retry configuration
      task_count  = 1
      parallelism = 1
      
      task_timeout = "1800s"  # 30 minutes timeout
    }
  }

  depends_on = [
    google_project_service.run_api
  ]
}

# Cloud Scheduler Job for Daily Update
resource "google_cloud_scheduler_job" "daily_stock_update" {
  name             = "stock-code-daily-update"
  description      = "Daily stock price update job"
  schedule         = "0 16 * * 1-5"  # 16:00 JST on weekdays
  time_zone        = "Asia/Tokyo"
  attempt_deadline = "3600s"  # 1 hour deadline

  retry_config {
    retry_count          = 3
    max_retry_duration   = "7200s"  # 2 hours max retry duration
    min_backoff_duration = "60s"
    max_backoff_duration = "600s"
    max_doublings        = 3
  }

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.daily_stock_update.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler_sa.email
    }

    headers = {
      "Content-Type" = "application/json"
    }
  }

  depends_on = [
    google_project_service.scheduler_api,
    google_cloud_run_v2_job.daily_stock_update
  ]
}

# Secret Manager for sensitive data
resource "google_secret_manager_secret" "secret_key" {
  secret_id = "stock-code-secret-key"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret" "slack_webhook" {
  secret_id = "stock-code-slack-webhook"
  
  replication {
    automatic = true
  }
}

# IAM for Secret Manager access
resource "google_secret_manager_secret_iam_member" "secret_key_accessor" {
  secret_id = google_secret_manager_secret.secret_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "slack_webhook_accessor" {
  secret_id = google_secret_manager_secret.slack_webhook.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

# Outputs
output "scheduler_job_name" {
  description = "Name of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.daily_stock_update.name
}

output "cloud_run_job_name" {
  description = "Name of the Cloud Run job"
  value       = google_cloud_run_v2_job.daily_stock_update.name
}

output "scheduler_service_account" {
  description = "Email of the scheduler service account"
  value       = google_service_account.scheduler_sa.email
}