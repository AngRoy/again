# Start only a Cloudflare Quick Tunnel to the local Again backend.
# This demo endpoint is temporary and works only while this machine/server remain running.
[CmdletBinding()]
param(
 [string]$CloudflaredPath='cloudflared.exe',
 [string]$StateDirectory=(Join-Path $PSScriptRoot '..\.runtime'),
 [ValidateRange(1024,65535)][int]$Port=7860
)
$ErrorActionPreference='Stop'
$projectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$StateDirectory=[IO.Path]::GetFullPath($StateDirectory)
[IO.Directory]::CreateDirectory($StateDirectory)|Out-Null
$resolvedCloudflared=(Get-Command $CloudflaredPath -ErrorAction Stop).Source
$tag=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmss')
$stdout=Join-Path $StateDirectory ($tag+'_tunnel_stdout.log')
$stderr=Join-Path $StateDirectory ($tag+'_tunnel_stderr.log')
$process=Start-Process -FilePath $resolvedCloudflared -ArgumentList @('tunnel','--url',('http://127.0.0.1:'+$Port),'--no-autoupdate','--protocol','http2') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
$identity=[ordered]@{pid=$process.Id;creation_filetime=$process.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();stdout=$stdout;stderr=$stderr;url=$null;temporary=$true;local_port=$Port}
$deadline=[DateTime]::UtcNow.AddSeconds(60)
while([DateTime]::UtcNow -lt $deadline){
 if($process.HasExited){throw ('Cloudflared exited; inspect '+$stderr)}
 $log=if(Test-Path -LiteralPath $stderr){Get-Content -LiteralPath $stderr -Raw}else{''}
 if($log -match 'https://[a-z0-9-]+\.trycloudflare\.com'){$identity.url=$Matches[0];break}
 Start-Sleep -Milliseconds 500
}
[IO.File]::WriteAllText((Join-Path $StateDirectory 'tunnel.json'),($identity|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
if(-not $identity.url){throw ('No public URL returned within 60 seconds; owned process identity and logs saved in '+$StateDirectory)}
Write-Output $identity.url
Write-Output 'Keep the backend and laptop running. Stop the saved PID only after matching its creation time.'
