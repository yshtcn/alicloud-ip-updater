# Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# ����Ƿ��Թ���ԱȨ������
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    # �������ԱȨ��
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# �л����ű�����Ŀ¼
Set-Location $PSScriptRoot

Write-Host "��ǰĿ¼���л�Ϊ�ű�����Ŀ¼: $PSScriptRoot"

# ��ȡ��ǰ���ں�ʱ��
$dateTime = Get-Date -Format "yyyyMMdd"
Write-Host "��ǰ����: $dateTime"

# ������ʾ����ȡ�汾�����һλ
$revision = Read-Host -Prompt "���������İ汾�� ($dateTime,���û�дΣ���ֱ�ӻس�)"
Write-Host "����İ汾��: $revision"

# �����汾��
if ([string]::IsNullOrWhiteSpace($revision)) {
    $version = "$dateTime"
} else {
    $version = "$dateTime" + "_$revision"
}
Write-Host "�����İ汾��: $version"

# ���������ϰ汾�ű�ǩ�� Docker ����
Write-Host "���ڹ��� Docker ����..."
$tempFileBuild = [System.IO.Path]::GetTempFileName()
docker build -t yshtcn/alicloud_ip_updater:$version . 2> $tempFileBuild

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker ���񹹽�ʧ��" -ForegroundColor Red
    Write-Host (Get-Content $tempFileBuild) -ForegroundColor Red
    Remove-Item $tempFileBuild
    exit
}
Write-Host "Docker ���񹹽��ɹ�"
Remove-Item $tempFileBuild

# ���ʹ��а汾�ű�ǩ�� Docker ���� Docker Hub
Write-Host "�������� Docker ���� Docker Hub..."
$tempFilePush = [System.IO.Path]::GetTempFileName()
docker push yshtcn/alicloud_ip_updater:$version 2> $tempFilePush

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker ��������ʧ��" -ForegroundColor Red
    Write-Host (Get-Content $tempFilePush) -ForegroundColor Red
    Remove-Item $tempFilePush
    exit
}
Write-Host "Docker �������ͳɹ�"
Remove-Item $tempFilePush

# Ϊ������� 'latest' ��ǩ������
Write-Host "����Ϊ������� 'latest' ��ǩ������..."
$tempFilePushLatest = [System.IO.Path]::GetTempFileName()
docker tag yshtcn/alicloud_ip_updater:$version yshtcn/alicloud_ip_updater:latest
docker push yshtcn/alicloud_ip_updater:latest 2> $tempFilePushLatest

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker ���� 'latest' ��ǩ����ʧ��" -ForegroundColor Red
    Write-Host (Get-Content $tempFilePushLatest) -ForegroundColor Red
    Remove-Item $tempFilePushLatest
    exit
}
Write-Host "Docker ���� 'latest' ��ǩ���ͳɹ�"
Remove-Item $tempFilePushLatest

Write-Host "Docker ���񹹽�����������ȫ�����"
