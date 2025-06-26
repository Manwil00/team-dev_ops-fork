# Database Setup Script for Niche Explorer Platform
# This script handles database initialization and management
# Migrations are handled automatically by Spring Boot on startup

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("init", "reset", "status", "start")]
    [string]$Action = "init",

    [Parameter(Mandatory=$false)]
    [string]$DbHost = "localhost",

    [Parameter(Mandatory=$false)]
    [string]$DbPort = "5432",

    [Parameter(Mandatory=$false)]
    [string]$DbName = "niche",

    [Parameter(Mandatory=$false)]
    [string]$DbUser = "niche_user",

    [Parameter(Mandatory=$false)]
    [string]$DbPassword = "niche_pass"
)

$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host " $Title" -ForegroundColor Yellow
    Write-Host "=" * 60 -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message)
    Write-Host "→ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "  $Message" -ForegroundColor Gray
}

function Test-DatabaseConnection {
    Write-Step "Testing database connection..."
    try {
        $containerName = "team-dev_ops-db-1"
        $testResult = docker exec $containerName pg_isready -h localhost -p 5432 -U $DbUser -d $DbName 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Info "Database connection successful"
            return $true
        } else {
            Write-Info "Database not ready"
            return $false
        }
    } catch {
        Write-Info "Database container not running"
        return $false
    }
}

function Start-DatabaseContainer {
    Write-Step "Starting database container..."
    docker compose up db -d

    Write-Step "Waiting for database to be ready..."
    $maxAttempts = 30
    $attempt = 0

    do {
        Start-Sleep -Seconds 2
        $attempt++
        Write-Info "Attempt $attempt/$maxAttempts"
    } while (-not (Test-DatabaseConnection) -and $attempt -lt $maxAttempts)

    if (-not (Test-DatabaseConnection)) {
        throw "Database failed to start after $maxAttempts attempts"
    }

    Write-Info "Database is ready!"
}

function Show-DatabaseStatus {
    Write-Step "Checking database status..."

    # Check container status
    $containerStatus = docker ps --filter "name=team-dev_ops-db-1" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Info "Container Status:"
    Write-Host "  $containerStatus" -ForegroundColor White

    # Check connection
    if (Test-DatabaseConnection) {
        Write-Info "Database connection: ✅ Connected"

        # Show table information if available
        Write-Step "Checking database schema..."
        try {
            # Check if tables exist
            $tablesExist = docker exec team-dev_ops-db-1 psql -U $DbUser -d $DbName -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'analysis');" 2>$null

            if ($tablesExist.Trim() -eq "t") {
                Write-Info "Schema: ✅ Tables exist"

                # Show table counts
                $analysisCount = docker exec team-dev_ops-db-1 psql -U $DbUser -d $DbName -t -c "SELECT COUNT(*) FROM analysis;" 2>$null
                $trendCount = docker exec team-dev_ops-db-1 psql -U $DbUser -d $DbName -t -c "SELECT COUNT(*) FROM trend;" 2>$null

                Write-Info "Analysis records: $($analysisCount.Trim())"
                Write-Info "Trend records: $($trendCount.Trim())"
            } else {
                Write-Info "Schema: ⚠️  Tables not created yet (will be created when API server starts)"
            }
        } catch {
            Write-Info "Could not check database schema"
        }
    } else {
        Write-Info "Database connection: ❌ Not connected"
    }
}

function Initialize-Database {
    Write-Header "Initializing Niche Explorer Database"

    if (-not (Test-DatabaseConnection)) {
        Start-DatabaseContainer
    } else {
        Write-Step "Database already running"
    }

    Write-Step "Database initialization complete!"
    Write-Info ""
    Write-Info "💡 Note: Database migrations are handled automatically by Spring Boot"
    Write-Info "   when the API server starts up."
    Write-Info ""
    Write-Info "To start the complete application:"
    Write-Info "  docker compose up -d"
    Write-Info ""
    Write-Info "To start just the database:"
    Write-Info "  docker compose up db -d"
}

function Reset-Database {
    Write-Header "Resetting Niche Explorer Database"
    Write-Host "⚠️  WARNING: This will delete all data!" -ForegroundColor Red

    $confirmation = Read-Host "Are you sure you want to reset the database? (yes/no)"
    if ($confirmation -ne "yes") {
        Write-Host "Database reset cancelled" -ForegroundColor Yellow
        return
    }

    Write-Step "Stopping services..."
    docker compose down

    Write-Step "Removing database volume..."
    docker volume rm team-dev_ops_postgres_data 2>$null

    Write-Step "Starting fresh database..."
    Start-DatabaseContainer

    Write-Info ""
    Write-Info "✅ Database reset complete!"
    Write-Info "   Start the API server to run migrations: docker compose up api-server -d"
}

function Start-Application {
    Write-Header "Starting Niche Explorer Application"

    Write-Step "Starting all services..."
    docker compose up -d

    Write-Step "Waiting for services to be ready..."
    Start-Sleep -Seconds 5

    Write-Info ""
    Write-Info "🚀 Application started!"
    Write-Info "   Frontend: http://localhost:3000"
    Write-Info "   API Server: http://localhost:8080"
    Write-Info "   GenAI Service: http://localhost:8000"
    Write-Info ""
    Write-Info "Check service status: docker compose ps"
}

function Show-Help {
    Write-Header "Niche Explorer Database Management"

    Write-Host "DESCRIPTION:" -ForegroundColor Yellow
    Write-Host "  Manages the Niche Explorer database and application startup." -ForegroundColor White
    Write-Host "  Database migrations are handled automatically by Spring Boot." -ForegroundColor White
    Write-Host ""
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  .\setup-database.ps1 [-Action <action>] [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "ACTIONS:" -ForegroundColor Yellow
    Write-Host "  init     Initialize database only (default)" -ForegroundColor White
    Write-Host "  start    Start complete application stack" -ForegroundColor White
    Write-Host "  status   Show database and application status" -ForegroundColor White
    Write-Host "  reset    Reset database (deletes all data)" -ForegroundColor White
    Write-Host ""
    Write-Host "OPTIONS:" -ForegroundColor Yellow
    Write-Host "  -DbHost      Database host (default: localhost)" -ForegroundColor White
    Write-Host "  -DbPort      Database port (default: 5432)" -ForegroundColor White
    Write-Host "  -DbName      Database name (default: niche)" -ForegroundColor White
    Write-Host "  -DbUser      Database user (default: niche_user)" -ForegroundColor White
    Write-Host "  -DbPassword  Database password (default: niche_pass)" -ForegroundColor White
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  .\setup-database.ps1                    # Initialize database" -ForegroundColor Gray
    Write-Host "  .\setup-database.ps1 -Action start      # Start full application" -ForegroundColor Gray
    Write-Host "  .\setup-database.ps1 -Action status     # Check status" -ForegroundColor Gray
    Write-Host "  .\setup-database.ps1 -Action reset      # Reset database" -ForegroundColor Gray
    Write-Host ""
    Write-Host "MIGRATION NOTES:" -ForegroundColor Yellow
    Write-Host "  • Database schema is managed by Spring Boot + Flyway" -ForegroundColor Gray
    Write-Host "  • Migrations run automatically when API server starts" -ForegroundColor Gray
    Write-Host "  • Migration file: server/src/api-server/src/main/resources/db/migration/V1__unified_database_schema.sql" -ForegroundColor Gray
}

# Main execution
try {
    switch ($Action.ToLower()) {
        "init" {
            Initialize-Database
        }
        "start" {
            Start-Application
        }
        "status" {
            Show-DatabaseStatus
        }
        "reset" {
            Reset-Database
        }
        "help" {
            Show-Help
        }
        default {
            Write-Host "Unknown action: $Action" -ForegroundColor Red
            Show-Help
            exit 1
        }
    }
} catch {
    Write-Host ""
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "For help, run: .\setup-database.ps1 -Action help" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✅ Operation completed successfully!" -ForegroundColor Green
