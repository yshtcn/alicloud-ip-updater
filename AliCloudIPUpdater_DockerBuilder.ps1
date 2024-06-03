# Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 检查是否以管理员权限运行
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    # 请求管理员权限
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# 切换到脚本所在目录
Set-Location $PSScriptRoot

Write-Host "当前目录已切换为脚本所在目录: $PSScriptRoot"

# 获取当前日期和时间
$dateTime = Get-Date -Format "yyyyMMdd"
Write-Host "当前日期: $dateTime"

# 输入提示并获取版本的最后一位
$revision = Read-Host -Prompt "请输入今天的版本次 ($dateTime,如果没有次，请直接回车)"
Write-Host "输入的版本次: $revision"

# 构建版本号
if ([string]::IsNullOrWhiteSpace($revision)) {
    $version = "$dateTime"
} else {
    $version = "$dateTime" + "_$revision"
}
Write-Host "构建的版本号: $version"

# 构建并打上版本号标签的 Docker 镜像
Write-Host "正在构建 Docker 镜像..."
$tempFileBuild = [System.IO.Path]::GetTempFileName()
docker build -t yshtcn/alicloud_ip_updater:$version . 2> $tempFileBuild

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker 镜像构建失败" -ForegroundColor Red
    Write-Host (Get-Content $tempFileBuild) -ForegroundColor Red
    Remove-Item $tempFileBuild
    exit
}
Write-Host "Docker 镜像构建成功"
Remove-Item $tempFileBuild

# 推送带有版本号标签的 Docker 镜像到 Docker Hub
Write-Host "正在推送 Docker 镜像到 Docker Hub..."
$tempFilePush = [System.IO.Path]::GetTempFileName()
docker push yshtcn/alicloud_ip_updater:$version 2> $tempFilePush

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker 镜像推送失败" -ForegroundColor Red
    Write-Host (Get-Content $tempFilePush) -ForegroundColor Red
    Remove-Item $tempFilePush
    exit
}
Write-Host "Docker 镜像推送成功"
Remove-Item $tempFilePush

# 为镜像打上 'latest' 标签并推送
Write-Host "正在为镜像打上 'latest' 标签并推送..."
$tempFilePushLatest = [System.IO.Path]::GetTempFileName()
docker tag yshtcn/alicloud_ip_updater:$version yshtcn/alicloud_ip_updater:latest
docker push yshtcn/alicloud_ip_updater:latest 2> $tempFilePushLatest

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker 镜像 'latest' 标签推送失败" -ForegroundColor Red
    Write-Host (Get-Content $tempFilePushLatest) -ForegroundColor Red
    Remove-Item $tempFilePushLatest
    exit
}
Write-Host "Docker 镜像 'latest' 标签推送成功"
Remove-Item $tempFilePushLatest

Write-Host "Docker 镜像构建和推送流程全部完成"
