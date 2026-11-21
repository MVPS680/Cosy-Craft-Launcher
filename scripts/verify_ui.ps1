param([Parameter(Mandatory = $true)][string]$Exe)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase
$assembly = [Reflection.Assembly]::Load([IO.File]::ReadAllBytes($Exe))
[Windows.Application]::ResourceAssembly = $assembly
$app = [Activator]::CreateInstance($assembly.GetType('PCL.Application'), $true)
$app.InitializeComponent()
# Run only a test host, never the launcher's real Startup/auth/network/settings flow.
$startup = $app.GetType().GetMethod('Application_Startup', [Reflection.BindingFlags]'Instance,NonPublic')
$startupHandler = [Delegate]::CreateDelegate([Windows.StartupEventHandler], $app, $startup)
$app.remove_Startup($startupHandler)
$startupUriField = [Windows.Application].GetField('_startupUri', [Reflection.BindingFlags]'Instance,NonPublic')
if ($null -eq $startupUriField) { throw 'Cannot isolate WPF startup; test host was not shown.' }
$startupUriField.SetValue($app, $null)
[PCL.ModAnimation]::AniControlEnabled = 1
$script:checks = 0
function Assert-UI([bool]$condition, [string]$message) {
    if (-not $condition) { throw "FAIL: $message" }
    $script:checks++
    Write-Output "PASS: $message"
}
function Send-TestKey($target, [Windows.Input.Key]$key, [bool]$keyUp = $false) {
    $event = [Windows.Input.KeyEventArgs]::new([Windows.Input.Keyboard]::PrimaryDevice,
        [Windows.PresentationSource]::FromVisual($target), 0, $key)
    $event.RoutedEvent = if ($keyUp) { [Windows.Input.Keyboard]::KeyUpEvent } else { [Windows.Input.Keyboard]::KeyDownEvent }
    $target.RaiseEvent($event)
}
function Contrast-OnWhite([Windows.Media.Color]$color) {
    $channels = @($color.R, $color.G, $color.B) | ForEach-Object {
        # Include the brightest 5% white sheen used by the primary button.
        $value = (0.95 * $_ + 0.05 * 255) / 255
        if ($value -le 0.04045) { $value / 12.92 } else { [Math]::Pow(($value + 0.055) / 1.055, 2.4) }
    }
    return 1.05 / (0.2126*$channels[0] + 0.7152*$channels[1] + 0.0722*$channels[2] + 0.05)
}
Assert-UI ((Contrast-OnWhite $app.Resources['ColorBrush2'].Color) -ge 4.5) 'default primary fill preserves white text contrast'
Assert-UI ((Contrast-OnWhite $app.Resources['ColorBrushPrimaryHover'].Color) -ge 4.5) 'default hover fill preserves white text contrast'
$infoHint = [PCL.MyHint]::new()
$infoHint.Theme = [PCL.MyHint+Themes]::Blue
$errorHint = [PCL.MyHint]::new()
$errorHint.Theme = [PCL.MyHint+Themes]::Red
Assert-UI ($infoHint.BorderBrush.ToString() -ne $errorHint.BorderBrush.ToString()) 'informational hints are distinct from errors'
$hostWindow = [Windows.Window]::new()
$hostWindow.Title = 'Cosy Craft Launcher local UI regression host'
$hostWindow.ShowInTaskbar = $false
$hostWindow.Left = -16000
$hostWindow.Top = -16000
$hostWindow.Width = 600
$hostWindow.Height = 500
$panel = [Windows.Controls.StackPanel]::new()
$hostWindow.Content = $panel
$button = [PCL.MyButton]::new()
$button.Text = 'Test action'
$button.Height = 36
$button.Width = 160
$script:clicks = 0
$button.add_Click({ $script:clicks++ })
$panel.Children.Add($button) | Out-Null
$other = [PCL.MyButton]::new()
$other.Text = 'Other action'
$other.Height = 36
$panel.Children.Add($other) | Out-Null
$checkbox = [PCL.MyCheckBox]::new()
$checkbox.Text = 'Test setting without a settings key'
$panel.Children.Add($checkbox) | Out-Null
$radioA = [PCL.MyRadioButton]::new()
$radioA.Text = 'A'
$radioB = [PCL.MyRadioButton]::new()
$radioB.Text = 'B'
$radioGroup = [Windows.Controls.StackPanel]::new()
$radioGroup.Children.Add($radioA) | Out-Null
$radioGroup.Children.Add($radioB) | Out-Null
$panel.Children.Add($radioGroup) | Out-Null
$radioA.Checked = $true
$combo = [PCL.MyComboBox]::new()
$combo.Height = 32
$combo.Items.Add('Example version') | Out-Null
$combo.SelectedIndex = 0
$panel.Children.Add($combo) | Out-Null

try {
    $hostWindow.Show()
    $hostWindow.UpdateLayout()
    $button.Focus() | Out-Null
    Assert-UI $button.IsKeyboardFocused 'button accepts keyboard focus'
    Assert-UI ($null -ne $button.FocusVisualStyle) 'button has a keyboard focus ring'
    Send-TestKey $button Enter
    Assert-UI ($script:clicks -eq 1) 'Enter invokes button once'
    Send-TestKey $button Space
    Assert-UI ($script:clicks -eq 1) 'Space waits for key release'
    Send-TestKey $button Space $true
    Assert-UI ($script:clicks -eq 2) 'Space release invokes button once'
    Send-TestKey $button Space
    $other.Focus() | Out-Null
    Send-TestKey $button Space $true
    Assert-UI ($script:clicks -eq 2) 'losing focus cancels pending Space activation'
    $button.IsEnabled = $false
    Send-TestKey $button Enter
    Assert-UI ($script:clicks -eq 2) 'disabled button cannot activate'
    $checkbox.Focus() | Out-Null
    Send-TestKey $checkbox Space
    Assert-UI $checkbox.Checked 'Space toggles checkbox'
    $checkbox.add_PreviewChange({ param($sender, $eventArgs) $eventArgs.Handled = $true })
    $checkbox.SetChecked($false, $false)
    Send-TestKey $checkbox Space
    Assert-UI (-not $checkbox.Checked) 'keyboard checkbox respects PreviewChange cancellation'
    $radioB.Focus() | Out-Null
    Send-TestKey $radioB Enter
    Assert-UI ($radioB.Checked -and -not $radioA.Checked) 'keyboard radio activation preserves mutual exclusion'
    $combo.Focus() | Out-Null
    $combo.RefreshColor()
    Assert-UI ($combo.BorderBrush.ToString() -eq $app.Resources['ColorBrush3'].ToString()) 'combo focus changes its actual border'
    $other.Focus() | Out-Null
    $combo.RefreshColor()
    Assert-UI ($combo.BorderBrush.ToString() -eq $app.Resources['ColorBrushSoftBorder'].ToString()) 'combo blur restores idle border'
    Assert-UI ($combo.Foreground.ToString() -eq $app.Resources['ColorBrushTextPrimary'].ToString()) 'combo text stays readable independently of border'
    $editable = [PCL.MyComboBox]::new()
    $editable.IsEditable = $true
    $editable.RefreshColor()
    $panel.Children.Add($editable) | Out-Null
    $editable.ApplyTemplate() | Out-Null
    Assert-UI ($null -ne $editable.Template.FindName('PART_EditableTextBox', $editable)) 'editable combo applies template without a null-focus error'
    Assert-UI ($null -eq [PCL.ModMain]::FrmMain) 'launcher main window and account startup were not created'
} finally {
    $hostWindow.Close()
}

# Layout checks use the compiled page directly, without Loaded handlers.
$launchPage = [PCL.PageLaunchRight]::new()
$launchPage.FindName('PanHint').Visibility = 'Collapsed'
$launchPage.FindName('PanLog').Visibility = 'Collapsed'
foreach ($width in @(450, 680)) {
    $launchPage.Measure([Windows.Size]::new($width, 640))
    $launchPage.Arrange([Windows.Rect]::new(0, 0, $width, 640))
    $launchPage.UpdateLayout()
    $card = $launchPage.FindName('PanWelcome')
    foreach ($name in @('BtnWelcomeDownload','BtnWelcomePack','BtnWelcomeSetup')) {
        $entry = $launchPage.FindName($name)
        $point = $entry.TranslatePoint([Windows.Point]::new(0,0), $card)
        Assert-UI ($point.X -ge 0 -and $point.X + $entry.ActualWidth -le $card.ActualWidth) "$name fits at $width DIP"
    }
}
$welcome = $launchPage.FindName('PanWelcome')
$guide = $launchPage.FindName('PanWelcomeGuide')
$welcome.Visibility = 'Collapsed'
$guide.GetBindingExpression([Windows.UIElement]::VisibilityProperty).UpdateTarget()
Assert-UI ($guide.Visibility -eq 'Collapsed') 'custom homepage mode also hides the built-in guide'
$sidebar = [PCL.PageLaunchLeft]::new()
$caption = $sidebar.FindName('LabVersion')
Assert-UI ($caption.Foreground.ToString() -eq $app.Resources['ColorBrushTextTertiary'].ToString()) 'disabled launch caption stays readable on a light button'
$sidebar.FindName('BtnLaunch').IsEnabled = $true
Assert-UI ($caption.Foreground.ToString() -eq $app.Resources['ColorBrushOnAccent'].ToString()) 'enabled launch caption uses white on the primary fill'
Write-Output "All $script:checks native UI checks passed. No launcher startup or authentication was executed."
