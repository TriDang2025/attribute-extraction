# Keeps Windows from idle-sleeping while results/.keep_awake exists (at most 30 hours).
# Uses SetThreadExecutionState, the call media players use; no power settings are changed.
$flag = Join-Path $PSScriptRoot "..\results\.keep_awake"
Add-Type -Namespace Win32 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
$ES_CONTINUOUS = [uint32]"0x80000000"; $ES_SYSTEM_REQUIRED = [uint32]"0x00000001"
$deadline = (Get-Date).AddHours(30)
while ((Test-Path $flag) -and ((Get-Date) -lt $deadline)) {
    [void][Win32.Power]::SetThreadExecutionState($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED)
    Start-Sleep -Seconds 60
}
[void][Win32.Power]::SetThreadExecutionState($ES_CONTINUOUS)
