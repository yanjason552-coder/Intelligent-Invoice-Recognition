param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Username = "test@example.com",
    [string]$Password = "test123456"
)

Write-Host "=== Invoice Query Test ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Login
Write-Host "[1/6] Logging in..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = $Username
        password = $Password
    }
    
    $loginResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/login/access-token" `
        -Method Post `
        -ContentType "application/x-www-form-urlencoded" `
        -Body $loginBody `
        -ErrorAction Stop
    
    $token = $loginResponse.access_token
    $headers = @{ "Authorization" = "Bearer $token" }
    Write-Host "  [OK] Login successful" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Helper function to build query URL
function Build-QueryUrl {
    param(
        [string]$BaseUrl,
        [hashtable]$Params
    )
    
    $queryParts = @()
    foreach ($key in $Params.Keys) {
        if ($Params[$key] -ne $null -and $Params[$key] -ne "") {
            $value = [System.Uri]::EscapeDataString($Params[$key])
            $queryParts += "$key=$value"
        }
    }
    
    $separator = [char]38
    $queryString = $queryParts -join $separator
    return "$BaseUrl/api/v1/invoices/query?$queryString"
}

# Helper function to execute query
function Invoke-Query {
    param(
        [string]$Url,
        [hashtable]$Headers,
        [string]$Description
    )
    
    Write-Host "  Query: $Description" -ForegroundColor Gray
    Write-Host "  URL: $Url" -ForegroundColor DarkGray
    
    try {
        $response = Invoke-RestMethod -Uri $Url -Method Get -Headers $Headers -ErrorAction Stop
        Write-Host "  [OK] Found $($response.count) records" -ForegroundColor Green
        
        if ($response.count -gt 0 -and $response.data) {
            Write-Host "  Sample records:" -ForegroundColor Cyan
            $response.data | Select-Object -First 3 | ForEach-Object {
                $invoiceNo = $_.invoice_no
                $invoiceType = $_.invoice_type
                $recognitionStatus = $_.recognition_status
                $reviewStatus = $_.review_status
                Write-Host "    - Invoice No: $invoiceNo" -ForegroundColor Gray
                Write-Host "      Type: $invoiceType, Recognition: $recognitionStatus, Review: $reviewStatus" -ForegroundColor DarkGray
            }
        } else {
            Write-Host "  No records found" -ForegroundColor Yellow
        }
        Write-Host ""
        return $response
    } catch {
        Write-Host "  [ERROR] Query failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        return $null
    }
}

# Test 2: Query all invoices (no filters)
Write-Host "[2/6] Test: Query all invoices (no filters)..." -ForegroundColor Yellow
$url = Build-QueryUrl -BaseUrl $BaseUrl -Params @{skip=0; limit=10}
Invoke-Query -Url $url -Headers $headers -Description "All invoices"
Write-Host ""

# Test 3: Query by invoice number (partial match)
Write-Host "[3/6] Test: Query by invoice number (partial match)..." -ForegroundColor Yellow
$url = Build-QueryUrl -BaseUrl $BaseUrl -Params @{skip=0; limit=10; invoice_no="INV-2025"}
Invoke-Query -Url $url -Headers $headers -Description "Invoice number contains 'INV-2025'"
Write-Host ""

# Test 4: Query by review status
Write-Host "[4/6] Test: Query by review status..." -ForegroundColor Yellow
$url = Build-QueryUrl -BaseUrl $BaseUrl -Params @{skip=0; limit=10; review_status="pending"}
Invoke-Query -Url $url -Headers $headers -Description "Review status = 'pending'"
Write-Host ""

# Test 5: Query by recognition status
Write-Host "[5/6] Test: Query by recognition status..." -ForegroundColor Yellow
$url = Build-QueryUrl -BaseUrl $BaseUrl -Params @{skip=0; limit=10; recognition_status="pending"}
Invoke-Query -Url $url -Headers $headers -Description "Recognition status = 'pending'"
Write-Host ""

# Test 6: Query with pagination
Write-Host "[6/6] Test: Query with pagination..." -ForegroundColor Yellow
Write-Host "  Testing pagination: skip=0, limit=5" -ForegroundColor Gray
$url1 = Build-QueryUrl -BaseUrl $BaseUrl -Params @{skip=0; limit=5}
$response1 = Invoke-Query -Url $url1 -Headers $headers -Description "First page (skip=0, limit=5)"

Write-Host "  Testing pagination: skip=5, limit=5" -ForegroundColor Gray
$url2 = Build-QueryUrl -BaseUrl $BaseUrl -Params @{skip=5; limit=5}
$response2 = Invoke-Query -Url $url2 -Headers $headers -Description "Second page (skip=5, limit=5)"
Write-Host ""

# Test 7: Combined filters (if we have test data)
Write-Host "[Bonus] Test: Combined filters..." -ForegroundColor Yellow
Write-Host "  Note: This test requires invoices with supplier/buyer data" -ForegroundColor Gray
$url = Build-QueryUrl -BaseUrl $BaseUrl -Params @{
    skip=0
    limit=10
    review_status="pending"
    recognition_status="pending"
}
Invoke-Query -Url $url -Headers $headers -Description "Combined: review_status='pending' AND recognition_status='pending'"
Write-Host ""

Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "All query tests completed!" -ForegroundColor Green
Write-Host ""

