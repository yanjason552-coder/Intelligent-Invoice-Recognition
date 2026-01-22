param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Username = "test@example.com",
    [string]$Password = "test123456",
    [string]$TestFile = "test_invoice.pdf"
)

Write-Host "=== Invoice Upload Test ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check backend service
Write-Host "[1/5] Checking backend service..." -ForegroundColor Yellow
try {
    $healthCheck = Invoke-WebRequest -Uri "$BaseUrl/docs" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  [OK] Backend service is running" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Backend service is not accessible: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Please start backend service: cd backend; uvicorn app.main:app --reload --port 8000" -ForegroundColor Yellow
    exit 1
}

# Step 2: Login to get token
Write-Host "[2/5] Logging in to get token..." -ForegroundColor Yellow
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
    Write-Host "  [OK] Login successful, token length: $($token.Length)" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Login failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        Write-Host "  Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
        try {
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $responseBody = $reader.ReadToEnd()
            $reader.Close()
            $stream.Close()
            Write-Host "  Error details: $responseBody" -ForegroundColor Yellow
            
            # Try to parse JSON error
            try {
                $errorObj = $responseBody | ConvertFrom-Json
                if ($errorObj.detail) {
                    Write-Host "  Detail: $($errorObj.detail)" -ForegroundColor Red
                }
            } catch {
                Write-Host "  (Could not parse error as JSON)" -ForegroundColor Gray
            }
        } catch {
            Write-Host "  (Could not read error response body)" -ForegroundColor Gray
        }
    }
    Write-Host "`n  Troubleshooting:" -ForegroundColor Cyan
    Write-Host "  1. Check if user exists: $Username" -ForegroundColor Gray
    Write-Host "  2. Check backend logs for detailed error" -ForegroundColor Gray
    Write-Host "  3. Verify database connection" -ForegroundColor Gray
    Write-Host "  4. Check if database migrations are applied" -ForegroundColor Gray
    exit 1
}

# Step 3: Create test file if not exists
Write-Host "[3/5] Preparing test file..." -ForegroundColor Yellow
if (-not (Test-Path $TestFile)) {
    Write-Host "  Creating test PDF file: $TestFile" -ForegroundColor Gray
    $pdfContent = @"
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Invoice) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000306 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
400
%%EOF
"@
    $pdfContent | Out-File -FilePath $TestFile -Encoding ASCII -NoNewline
    Write-Host "  [OK] Test file created" -ForegroundColor Green
} else {
    Write-Host "  [OK] Test file already exists: $TestFile" -ForegroundColor Green
}

# Step 4: Upload file
Write-Host "[4/5] Uploading invoice file..." -ForegroundColor Yellow
try {
    $filePath = Resolve-Path $TestFile
    $fileItem = Get-Item $filePath
    
    Write-Host "  File path: $filePath" -ForegroundColor Gray
    Write-Host "  File size: $($fileItem.Length) bytes" -ForegroundColor Gray
    
    Write-Host "  Sending upload request..." -ForegroundColor Gray
    
    # Method: Use .NET HttpClient for reliable multipart upload
    Add-Type -AssemblyName System.Net.Http
    
    $fileName = $fileItem.Name
    $httpClientHandler = New-Object System.Net.Http.HttpClientHandler
    $httpClient = New-Object System.Net.Http.HttpClient($httpClientHandler)
    $httpClient.DefaultRequestHeaders.Add("Authorization", "Bearer $token")
    
    $fileStream = $null
    try {
        # Create multipart form data
        $multipartContent = New-Object System.Net.Http.MultipartFormDataContent
        $fileStream = [System.IO.File]::OpenRead($filePath)
        $streamContent = New-Object System.Net.Http.StreamContent($fileStream)
        $streamContent.Headers.ContentType = New-Object System.Net.Http.Headers.MediaTypeHeaderValue("application/pdf")
        $multipartContent.Add($streamContent, "file", $fileName)
        
        Write-Host "  Uploading file using HttpClient..." -ForegroundColor Gray
        
        # Upload
        $response = $httpClient.PostAsync("$BaseUrl/api/v1/invoices/upload", $multipartContent).Result
        
        if ($response.IsSuccessStatusCode) {
            $responseContent = $response.Content.ReadAsStringAsync().Result
            $responseBody = $responseContent | ConvertFrom-Json
            
            Write-Host "  [OK] Upload successful!" -ForegroundColor Green
            Write-Host "  Response: $($responseBody.message)" -ForegroundColor Gray
        } else {
            $errorContent = $response.Content.ReadAsStringAsync().Result
            Write-Host "  [ERROR] Upload failed with status: $($response.StatusCode)" -ForegroundColor Red
            Write-Host "  Error details: $errorContent" -ForegroundColor Yellow
            
            # Try to parse error JSON
            try {
                $errorObj = $errorContent | ConvertFrom-Json
                if ($errorObj.detail) {
                    Write-Host "  Detailed error: $($errorObj.detail)" -ForegroundColor Yellow
                }
            } catch {
                # Ignore JSON parse error
            }
            
            throw "Upload failed: $($response.StatusCode)"
        }
    } finally {
        if ($fileStream) { $fileStream.Close() }
        $httpClient.Dispose()
        $httpClientHandler.Dispose()
    }
    
} catch {
    Write-Host "  [ERROR] Upload failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        try {
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $responseBody = $reader.ReadToEnd()
            $reader.Close()
            $stream.Close()
            Write-Host "  Error details: $responseBody" -ForegroundColor Yellow
            
            try {
                $errorObj = $responseBody | ConvertFrom-Json
                if ($errorObj.detail) {
                    Write-Host "  Detailed error: $($errorObj.detail)" -ForegroundColor Yellow
                }
            } catch {
                # Ignore JSON parse error
            }
        } catch {
            Write-Host "  Could not read error response" -ForegroundColor Gray
        }
    }
    exit 1
}

# Step 5: Query uploaded invoices
Write-Host "[5/5] Querying uploaded invoices..." -ForegroundColor Yellow
try {
    $queryParams = @{
        skip = 0
        limit = 10
    }
    $queryParts = @()
    foreach ($key in $queryParams.Keys) {
        $queryParts += "$key=$($queryParams[$key])"
    }
    $separator = [char]38
    $queryString = $queryParts -join $separator
    $queryUrl = "$BaseUrl/api/v1/invoices/query?$queryString"
    $invoices = Invoke-RestMethod -Uri $queryUrl -Method Get -Headers $headers -ErrorAction Stop
    
    Write-Host "  [OK] Query successful" -ForegroundColor Green
    Write-Host "  Found $($invoices.count) invoice records" -ForegroundColor Gray
    
    if ($invoices.count -gt 0) {
        Write-Host "`n  Latest invoice info:" -ForegroundColor Cyan
        $latestInvoice = $invoices.data[0]
        Write-Host "    Invoice No: $($latestInvoice.invoice_no)" -ForegroundColor Gray
        Write-Host "    Invoice Type: $($latestInvoice.invoice_type)" -ForegroundColor Gray
        Write-Host "    Recognition Status: $($latestInvoice.recognition_status)" -ForegroundColor Gray
        Write-Host "    Review Status: $($latestInvoice.review_status)" -ForegroundColor Gray
        Write-Host "    Create Time: $($latestInvoice.create_time)" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "  [ERROR] Query failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        try {
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $responseBody = $reader.ReadToEnd()
            $reader.Close()
            $stream.Close()
            Write-Host "  Error details: $responseBody" -ForegroundColor Yellow
        } catch {
            # Ignore error reading response
        }
    }
}

Write-Host "`n=== Test Completed ===" -ForegroundColor Cyan
