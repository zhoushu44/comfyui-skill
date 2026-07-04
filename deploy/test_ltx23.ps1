param(
    [ValidateSet("5s", "10s")]
    [string]$Duration = "5s",
    [string]$RemoteDir = "/tmp/comfyui-skill-test",
    [string]$ComfyUIUrl = "http://127.0.0.1:8188"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$UploadTool = Join-Path $ProjectRoot "tools/sftp_upload.py"
$Runner = Join-Path $ProjectRoot "runners/run_ltx23_server.py"
$Asset = Join-Path $ProjectRoot "assets/beauty_ref.png"
$Workflow = Join-Path $ProjectRoot "workflows/ltx23_i2v_beauty_dancing_$Duration.json"

foreach ($Path in @($UploadTool, $Runner, $Asset, $Workflow)) {
    if (-not (Test-Path $Path)) {
        throw "Missing required file: $Path"
    }
}

$RemoteRunner = "$RemoteDir/run_ltx23_server.py"
$RemoteAsset = "/root/ComfyUI/input/beauty_ref.png"
$RemoteWorkflow = "$RemoteDir/ltx23_i2v_beauty_dancing_$Duration.json"
$MaxWait = if ($Duration -eq "10s") { 3600 } else { 1800 }
$RunCommand = "COMFYUI_URL='$ComfyUIUrl' python3 '$RemoteRunner' '$RemoteWorkflow' 15 $MaxWait"

python $UploadTool $Runner $RemoteRunner
python $UploadTool $Asset $RemoteAsset
python $UploadTool $Workflow $RemoteWorkflow $RunCommand
