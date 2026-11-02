param([Parameter(Mandatory=$true)][string]$Arquivo)
# Inspecao explicita com Defender. Nao remove quarentena nem altera protecoes.
$ErrorActionPreference = 'Stop'
$target = (Resolve-Path -LiteralPath $Arquivo).Path
Get-FileHash -LiteralPath $target -Algorithm SHA256 | Format-List
$status = Get-MpComputerStatus
if (-not $status.AntivirusEnabled -or -not $status.RealTimeProtectionEnabled) {
    throw 'Defender indisponivel/inativo. Solicite a TI uma verificacao com o antivirus corporativo ativo.'
}
Write-Host ('Assinaturas: '+$status.AntivirusSignatureVersion+' atualizadas em '+$status.AntivirusSignatureLastUpdated)
Start-MpScan -ScanType CustomScan -ScanPath $target
Write-Host 'Solicitacao de verificacao concluida. Confira o historico do antivirus e a politica da TI; isto nao certifica ausencia universal de malware.'
Get-MpThreatDetection | Where-Object { ($_.Resources -join ' ') -like ('*'+$target+'*') } | Format-List
