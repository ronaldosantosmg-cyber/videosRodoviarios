param([Parameter(Mandatory=$true)][string]$Arquivo,[Parameter(Mandatory=$true)][string]$Thumbprint,[Parameter(Mandatory=$true)][string]$TimestampUrl)
# Executar no PC/serviço do titular. Não exporta chave, altera confiança ou desativa proteções.
$ErrorActionPreference = 'Stop'
if ($TimestampUrl -notmatch '^https://') { throw 'Use um serviço HTTPS de carimbo de tempo do emissor.' }
$cert = Get-Item ("Cert:\CurrentUser\My\" + $Thumbprint)
if (-not $cert.HasPrivateKey) { throw 'Certificado sem chave de assinatura disponível.' }
if ($cert.Subject -notmatch '(?i)(^|,\s*)CN=Ronaldo Santos(,|$)') { throw 'O certificado deve identificar Ronaldo Santos.' }
if (-not ($cert.EnhancedKeyUsageList.ObjectId.Value -contains '1.3.6.1.5.5.7.3.3')) { throw 'Certificado não autorizado para assinatura de código.' }
$chain = New-Object System.Security.Cryptography.X509Certificates.X509Chain
$chain.ChainPolicy.RevocationMode = 'Online'
if (-not $chain.Build($cert)) { throw 'A cadeia de confiança/revogação do certificado não foi aprovada.' }
$signed = Set-AuthenticodeSignature -FilePath $Arquivo -Certificate $cert -HashAlgorithm SHA256 -TimestampServer $TimestampUrl
if ($signed.Status -ne 'Valid' -or $signed.SignerCertificate.Thumbprint -ne $cert.Thumbprint) { throw 'A assinatura Authenticode não foi validada.' }
Write-Host 'Assinatura Authenticode validada: Ronaldo Santos.'
