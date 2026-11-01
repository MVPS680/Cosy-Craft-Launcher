param([Parameter(Mandatory = $true)][string]$Exe)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase
$assembly = [Reflection.Assembly]::Load([IO.File]::ReadAllBytes((Resolve-Path $Exe)))
[Windows.Application]::ResourceAssembly = $assembly
$app = [Activator]::CreateInstance($assembly.GetType('PCL.Application'), $true)
$app.InitializeComponent()
# Isolate the test window from launcher startup, accounts, downloads and saved settings.
$startup = $app.GetType().GetMethod('Application_Startup', [Reflection.BindingFlags]'Instance,NonPublic')
$app.remove_Startup([Delegate]::CreateDelegate([Windows.StartupEventHandler], $app, $startup))
$startupUri = [Windows.Application].GetField('_startupUri', [Reflection.BindingFlags]'Instance,NonPublic')
if (-not $startupUri) { throw 'Cannot isolate application startup.' }
$startupUri.SetValue($app, $null)
$entry = [PCL.Settings]::Entries['UiScarletMotion']
$entry.ValueCache[''] = $true
$script:checks = 0
function Assert-Theme([bool]$condition, [string]$message) {
    if (-not $condition) { throw "FAIL: $message" }
    $script:checks++
    Write-Output "PASS: $message"
}
function Pump {
    $frame = [Windows.Threading.DispatcherFrame]::new()
    $null = $app.Dispatcher.BeginInvoke([Windows.Threading.DispatcherPriority]::ApplicationIdle, [Action]{ $frame.Continue = $false })
    [Windows.Threading.Dispatcher]::PushFrame($frame)
}
$flags = [Reflection.BindingFlags]'Instance,NonPublic'
$motionField = [PCL.ScarletBackdrop].GetField('Motion', $flags)
$runningField = [PCL.ScarletBackdrop].GetField('Running', $flags)
$attachedField = [PCL.ScarletBackdrop].GetField('Attached', $flags)
$ownerField = [PCL.ScarletBackdrop].GetField('OwnerWindow', $flags)
$hostWindow = [Windows.Window]::new()
$hostWindow.Left = -16000
$hostWindow.Top = -16000
$hostWindow.ShowInTaskbar = $false
$hostWindow.Width = 480
$hostWindow.Height = 260
$panel = [Windows.Controls.StackPanel]::new()
$hostWindow.Content = $panel
$views = foreach ($mode in @('Title', 'Hero', 'Ribbon', 'Ambient')) {
    $view = [PCL.ScarletBackdrop]::new()
    $view.Mode = $mode
    $view.Height = 60
    $panel.Children.Add($view) | Out-Null
    $view
}
try {
    $theme = $assembly.GetType('PCL.ModSecret').GetMethod('ThemeRefresh', [Reflection.BindingFlags]'Static,Public,NonPublic')
    $theme.Invoke($null, @(-1)) | Out-Null
    Assert-Theme ($app.Resources['ColorBrush2'].Color.ToString() -eq '#FF963D63') 'runtime theme refresh preserves the refined accent palette'
    Assert-Theme ($app.Resources['ColorBrushCardSurface'] -is [Windows.Media.LinearGradientBrush]) 'shared cards and dialogs use the same layered surface'
    Assert-Theme ($entry.DefaultValue -eq $true) 'motion defaults to enabled'
    Assert-Theme ($entry.Source.ToString() -eq 'Normal') 'motion uses the normal persistent settings store'
    $hostWindow.Show()
    Pump
    $systemMotion = [Windows.SystemParameters]::ClientAreaAnimation -and -not [Windows.SystemParameters]::HighContrast
    foreach ($view in $views) {
        Assert-Theme (-not $view.IsHitTestVisible -and -not $view.Focusable) "$($view.Mode) decoration does not intercept input"
        Assert-Theme ($runningField.GetValue($view) -eq $systemMotion) "$($view.Mode) obeys system animation preferences"
        if ($systemMotion) {
            $motion = $motionField.GetValue($view)
            $motion.SeekAlignedToLastTick($view, [TimeSpan]::Zero, [Windows.Media.Animation.TimeSeekOrigin]::BeginTime)
            $before = $view.Background.GradientStops[0].Color.ToString()
            $motion.SeekAlignedToLastTick($view, [TimeSpan]::FromSeconds(7), [Windows.Media.Animation.TimeSeekOrigin]::BeginTime)
            Assert-Theme ($before -ne $view.Background.GradientStops[0].Color.ToString()) "$($view.Mode) native animation actually changes color"
            Assert-Theme ([Windows.Media.Animation.Timeline]::GetDesiredFrameRate($motion) -eq 24) "$($view.Mode) is capped at 24 fps"
            Assert-Theme ($motion.AutoReverse -and $motion.RepeatBehavior.HasCount -eq $false) "$($view.Mode) reverses smoothly without a loop jump"
        }
    }
    $entry.ValueCache[''] = $false
    $entry.OnChanged.Invoke($false)
    Pump
    foreach ($view in $views) {
        Assert-Theme (-not $runningField.GetValue($view)) "$($view.Mode) stops when preference is disabled"
        Assert-Theme (-not $view.Background.GradientStops[0].HasAnimatedProperties) "$($view.Mode) releases animation clocks"
    }
    $entry.ValueCache[''] = $true
    $entry.OnChanged.Invoke($true)
    Pump
    Assert-Theme ($runningField.GetValue($views[0]) -eq $systemMotion) 'preference change restores motion immediately'
    $hostWindow.WindowState = 'Minimized'
    Pump
    Assert-Theme (-not $runningField.GetValue($views[0])) 'minimized window stops motion'
    $hostWindow.WindowState = 'Normal'
    Pump
    Assert-Theme ($runningField.GetValue($views[0]) -eq $systemMotion) 'restoring window resumes motion'
    $hostWindow.Hide()
    Pump
    Assert-Theme (-not $runningField.GetValue($views[0])) 'hidden window stops motion'
    $hostWindow.Show()
    Pump
    Assert-Theme ($runningField.GetValue($views[0]) -eq $systemMotion) 'showing window resumes motion'
    $views[1].Visibility = 'Collapsed'
    Pump
    Assert-Theme (-not $runningField.GetValue($views[1])) 'hidden homepage decoration stops motion'
    $views[1].Visibility = 'Visible'
    Pump
    Assert-Theme ($runningField.GetValue($views[1]) -eq $systemMotion) 'visible homepage decoration resumes motion'
    $oldBrush = $views[0].Background
    $views[0].Mode = 'Hero'
    Pump
    Assert-Theme (-not $oldBrush.GradientStops[0].HasAnimatedProperties) 'replacing a palette releases old brush clocks'
    $panel.Children.Remove($views[1])
    Pump
    Assert-Theme (-not $attachedField.GetValue($views[1]) -and $null -eq $ownerField.GetValue($views[1])) 'unloading releases window and event subscriptions'
    $panel.Children.Add($views[1]) | Out-Null
    Pump
    Assert-Theme ($attachedField.GetValue($views[1]) -and $runningField.GetValue($views[1]) -eq $systemMotion) 'reloading attaches and resumes exactly once'
    $hostWindow.Close()
    Pump
    Assert-Theme (@($views | Where-Object { $attachedField.GetValue($_) -or $runningField.GetValue($_) }).Count -eq 0) 'closing cleans up all theme instances'
    Assert-Theme ($null -eq [PCL.ModMain]::FrmMain) 'launcher startup and account flow were not executed'
    Write-Output "All $script:checks theme checks passed. Saved settings were not modified."
} finally {
    $hostWindow.Close()
    $app.Shutdown()
}
