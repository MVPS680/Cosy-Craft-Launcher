'由于包含加解密等安全信息，本文件中的部分代码已被删除

Friend Module ModSecret

    '标注启动器的不同分支，仅用于替换标记
    Public Const VersionBranchMain As String = "Main"
    '在开源版的注册表与常规版的注册表隔离，以防数据冲突
    Public Const RegFolder As String = "PCLDebug"
    '用于微软登录的 ClientId
    Public OAuthClientId As String = If(Environment.GetEnvironmentVariable("COSY_MS_CLIENT_ID") <> "", Environment.GetEnvironmentVariable("COSY_MS_CLIENT_ID"),
        If(Environment.GetEnvironmentVariable("PCL_MS_CLIENT_ID") <> "", Environment.GetEnvironmentVariable("PCL_MS_CLIENT_ID"), "fe72edc2-3a6f-4280-90e8-e2beb64ce7e1"))
    'CurseForge API Key
    Public CurseForgeAPIKey As String = If(Environment.GetEnvironmentVariable("COSY_CURSEFORGE_API_KEY") <> "", Environment.GetEnvironmentVariable("COSY_CURSEFORGE_API_KEY"),
        If(Environment.GetEnvironmentVariable("PCL_CURSEFORGE_API_KEY") <> "", Environment.GetEnvironmentVariable("PCL_CURSEFORGE_API_KEY"), "$2a$10$7WWV1WELcwX8Xp7d68MHs.5grTyZVa6SynyeSyMh1rsE89nIa09zO"))
    '用于匿名数据收集的腾讯云日志服务上报 URL，形如 https://{region}.cls.tencentcs.com/track?topic_id={topic_id}
    Public Const ClsBaseUrl As String = ""

#Region "网络鉴权"

    Public Const RestrictMcDownload As Boolean = False
    Friend Function SecretCdnSign(UrlWithMark As String) As String
        If Not UrlWithMark.EndsWithF("{CDN}") Then Return UrlWithMark
        Return UrlWithMark.Replace("{CDN}", "").Replace(" ", "%20")
    End Function
    ''' <summary>
    ''' 设置 Headers 的 UA、Referer。
    ''' </summary>
    Friend Sub SecretHeadersSign(Url As String, ByRef Req As HttpRequestMessage, Optional SimulateBrowserHeaders As Boolean = False)
        If Not Req.Headers.UserAgent.Any Then
            If Url.Contains("baidupcs.com") OrElse Url.Contains("baidu.com") Then
                Req.Headers.Add("User-Agent", "LogStatistic")  '#4951
            ElseIf SimulateBrowserHeaders Then
                Req.Headers.Add("User-Agent", $"PCL2/{VersionBaseName}.{CInt(BuildType)} Mozilla/5.0 AppleWebKit/537.36 Chrome/63.0.3239.132 Safari/537.36")
            Else
                Req.Headers.Add("User-Agent", $"PCL2/{VersionBaseName}.{CInt(BuildType)}")
            End If
        End If
        If Not SimulateBrowserHeaders Then Req.Headers.Add("Referer", $"http://{VersionCode}.open.pcl2.server/")
        If Url.Contains("api.curseforge.com") OrElse Url.Contains("forgecdn.net") Then Req.Headers.Add("x-api-key", CurseForgeAPIKey)
    End Sub

#End Region

#Region "主题"

    Public Color1 As New MyColor(56,46,66)
    Public Color2 As New MyColor(150,61,99)
    Public Color3 As New MyColor(175,82,118)
    Public Color4 As New MyColor(189,120,148)
    Public Color5 As New MyColor(213,165,186)
    Public Color6 As New MyColor(234,211,224)
    Public Color7 As New MyColor(243,232,240)
    Public Color8 As New MyColor(249,243,247)
    Public ColorBg0 As New MyColor(225, 125, 133)
    Public ColorBg1 As New MyColor(190, Color7)
    Public ColorGray1 As New MyColor(64, 64, 64)
    Public ColorGray2 As New MyColor(115, 115, 115)
    Public ColorGray3 As New MyColor(140, 140, 140)
    Public ColorGray4 As New MyColor(166, 166, 166)
    Public ColorGray5 As New MyColor(204, 204, 204)
    Public ColorGray6 As New MyColor(235, 235, 235)
    Public ColorGray7 As New MyColor(240, 240, 240)
    Public ColorGray8 As New MyColor(245, 245, 245)
    Public ColorSemiTransparent As New MyColor(1, Color8)

    Public ThemeNow As Integer = -1
    ' 红魔馆双生主题：绯红交互色，月夜紫与暖红装饰背景
    Public ColorHue As Integer = 355, ColorSat As Integer = 80, ColorLightAdjust As Integer = -10, ColorHueTopbarDelta As OneOf(Of Integer, Integer()) = New Integer() {-9, 0, -3}
    Public ThemeDontClick As Integer = 0

    Public Sub ThemeRefresh(Optional NewTheme As Integer = -1)
        Try
            If NewTheme < 0 Then NewTheme = Settings.Get(Of Integer)("UiLauncherTheme")
            '主题 12、14 需要允许重复刷新（随机色 / 自定义滑块）
            If ThemeNow = NewTheme AndAlso NewTheme <> 12 AndAlso NewTheme <> 14 Then Return
            If Not ThemeCheckOne(NewTheme) Then Return
            ThemeNow = NewTheme

            '默认保持现有绯红色板；其余主题仅围绕该色板做有限的色相偏移
            ColorHue = 355
            ColorSat = 80
            ColorLightAdjust = -10
            ColorHueTopbarDelta = New Integer() {-9, 0, -3}
            Select Case NewTheme
                Case 1 : ColorHue = 330
                Case 2 : ColorHue = 40
                Case 3 : ColorHue = 25
                Case 4 : ColorHue = 350 : ColorLightAdjust = -12
                Case 5 : ColorSat = 0 : ColorLightAdjust = -18
                Case 6 : ColorHue = 330
                Case 7 : ColorHue = 290
                Case 8 : ColorHue = 40
                Case 9 : ColorHue = 20
                Case 10 : ColorHue = 355
                Case 11 : ColorHue = 220
                Case 12
                    ColorHue = RandomInteger(0, 359)
                    ColorSat = RandomInteger(70, 90)
                    ColorLightAdjust = RandomInteger(-14, -6)
                Case 13
                    ColorHue = RandomInteger(0, 359)
                    ColorSat = RandomInteger(70, 95)
                Case 14
                    ColorHue = Settings.Get(Of Integer)("UiLauncherHue")
                    ColorSat = Settings.Get(Of Integer)("UiLauncherSat")
                    ColorLightAdjust = Settings.Get(Of Integer)("UiLauncherLight") - 20
                    ColorHueTopbarDelta = Settings.Get(Of Integer)("UiLauncherDelta")
            End Select

            Color1 = New MyColor(56,46,66)
            Color2 = New MyColor(150,61,99)
            Color3 = New MyColor(175,82,118)
            Color4 = New MyColor(189,120,148)
            Color5 = New MyColor(213,165,186)
            Color6 = New MyColor(234,211,224)
            Color7 = New MyColor(243,232,240)
            Color8 = New MyColor(249,243,247)
            '强调色做有限的色相偏移，卡片表面（Color6-8）保持现有绯红色板
            If NewTheme <> 0 Then
                Color2 = New MyColor().FromHSL2(ColorHue, ColorSat, 43 + ColorLightAdjust)
                Color3 = New MyColor().FromHSL2(ColorHue, ColorSat, 55 + ColorLightAdjust)
                Color4 = New MyColor().FromHSL2(ColorHue, ColorSat, 67 + ColorLightAdjust)
            End If
            ColorBg0 = Color4 * 0.4 + Color5 * 0.4 + ColorGray4 * 0.2
            ColorBg1 = New MyColor(140, Color7)

            ColorSemiTransparent = New MyColor(1, Color8)
            Application.Current.Resources("ColorBrush1") = New SolidColorBrush(Color1)
            Application.Current.Resources("ColorBrush2") = New SolidColorBrush(Color2)
            Application.Current.Resources("ColorBrushPrimaryHover") = New SolidColorBrush(Color2 * 0.6 + Color3 * 0.4)
            Application.Current.Resources("ColorBrush3") = New SolidColorBrush(Color3)
            Application.Current.Resources("ColorBrush4") = New SolidColorBrush(Color4)
            Application.Current.Resources("ColorBrush5") = New SolidColorBrush(Color5)
            Application.Current.Resources("ColorBrush6") = New SolidColorBrush(Color6)
            Application.Current.Resources("ColorBrush7") = New SolidColorBrush(Color7)
            Application.Current.Resources("ColorBrush8") = New SolidColorBrush(Color8)
            Application.Current.Resources("ColorBrushBg0") = New SolidColorBrush(ColorBg0)
            Application.Current.Resources("ColorBrushBg1") = New SolidColorBrush(ColorBg1)
            Application.Current.Resources("ColorObject1") = CType(Color1, Color)
            Application.Current.Resources("ColorObject2") = CType(Color2, Color)
            Application.Current.Resources("ColorObject3") = CType(Color3, Color)
            Application.Current.Resources("ColorObject4") = CType(Color4, Color)
            Application.Current.Resources("ColorObject5") = CType(Color5, Color)
            Application.Current.Resources("ColorObject6") = CType(Color6, Color)
            Application.Current.Resources("ColorObject7") = CType(Color7, Color)
            Application.Current.Resources("ColorObject8") = CType(Color8, Color)
            Application.Current.Resources("ColorObjectBg0") = CType(ColorBg0, Color)
            Application.Current.Resources("ColorObjectBg1") = CType(ColorBg1, Color)
            ThemeRefreshMain()
        Catch ex As Exception
            Logger.Error(ex, "刷新主题颜色失败", LogBehavior.Toast)
        End Try
    End Sub
    Public Sub ThemeRefreshMain()
        RunInUi(
        Sub()
            If FrmMain Is Nothing OrElse Not FrmMain.IsLoaded Then Return
            '顶部条背景：半透明磨砂玻璃，让动态背景透上来
            Const TopbarAlpha As Double = 180
            Dim Brush = New LinearGradientBrush With {.EndPoint = New Point(1, 0), .StartPoint = New Point(0, 0)}
            Dim Deltas = ColorHueTopbarDelta.Switch(Function(d) New Integer() {-d, 0, d}, Function(d) d)
            Brush.GradientStops.Add(New GradientStop With {.Offset = -0.05, .Color = New MyColor(TopbarAlpha, New MyColor().FromHSL2(ColorHue + Deltas(0), ColorSat * 0.8, 39 + ColorLightAdjust))})
            Brush.GradientStops.Add(New GradientStop With {.Offset = 0.32, .Color = New MyColor(TopbarAlpha, New MyColor().FromHSL2(ColorHue + Deltas(1), ColorSat * 0.9, 48 + ColorLightAdjust))})
            Brush.GradientStops.Add(New GradientStop With {.Offset = 0.72, .Color = New MyColor(TopbarAlpha, New MyColor().FromHSL2(ColorHue + Deltas(2), ColorSat * 0.8, 44 + ColorLightAdjust))})
            Brush.GradientStops.Add(New GradientStop With {.Offset = 1.05, .Color = New MyColor(TopbarAlpha, New MyColor().FromHSL2(ColorHue + Deltas(2), ColorSat * 0.75, 38 + ColorLightAdjust))})
            FrmMain.PanTitle.Background = Brush
            FrmMain.PanTitle.Background.Freeze()
            FrmMain.ScarletAmbient.Visibility = If(Settings.Get(Of Boolean)("UiBackgroundColorful"), Visibility.Visible, Visibility.Collapsed)
            '主页面背景
            If Settings.Get(Of Boolean)("UiBackgroundColorful") Then
                Brush = New LinearGradientBrush With {.EndPoint = New Point(0.1, 1), .StartPoint = New Point(0.9, 0)}
                Brush.GradientStops.Add(New GradientStop With {.Offset = -0.1, .Color = New MyColor().FromHSL2(ColorHue - 15, ColorSat * 0.12, 97)})
                Brush.GradientStops.Add(New GradientStop With {.Offset = 0.4, .Color = New MyColor().FromHSL2(ColorHue, ColorSat * 0.15, 96.5)})
                Brush.GradientStops.Add(New GradientStop With {.Offset = 1.1, .Color = New MyColor().FromHSL2(ColorHue + 15, ColorSat * 0.1, 97)})
                FrmMain.PanForm.Background = Brush
            Else
                FrmMain.PanForm.Background = New MyColor(245, 245, 245)
            End If
            FrmMain.PanForm.Background.Freeze()
        End Sub)
    End Sub
    Friend Sub ThemeCheckAll(EffectSetup As Boolean)
        Try
            If FrmSetupUI Is Nothing Then Return
            Dim Themes() As MyRadioBox = {FrmSetupUI.RadioLauncherTheme5, FrmSetupUI.RadioLauncherTheme6,
                FrmSetupUI.RadioLauncherTheme7, FrmSetupUI.RadioLauncherTheme8, FrmSetupUI.RadioLauncherTheme9,
                FrmSetupUI.RadioLauncherTheme10, FrmSetupUI.RadioLauncherTheme11, FrmSetupUI.RadioLauncherTheme12,
                FrmSetupUI.RadioLauncherTheme13, FrmSetupUI.RadioLauncherTheme14}
            For Each Theme In Themes
                If Theme IsNot Nothing Then Theme.IsEnabled = True
            Next
        Catch ex As Exception
            Logger.Warn(ex, "刷新主题解锁状态失败")
        End Try
    End Sub
    Friend Function ThemeCheckOne(Id As Integer) As Boolean
        Return True
    End Function
    Friend Function ThemeUnlock(Id As Integer, Optional ShowDoubleHint As Boolean = True, Optional UnlockHint As String = Nothing) As Boolean
        '所有主题已直接开放，不再需要解锁流程
        Return False
    End Function

#End Region

#Region "更新"

    Friend Sub UpdateCheckByButton()
        Hint("该版本中不包含更新功能……")
    End Sub

    Friend IsUpdateWaitingRestart As Boolean = False
    Public Sub UpdateRestart(TriggerRestartAndByEnd As Boolean)
    End Sub
    Public Sub UpdateReplace(ProcessId As Integer, OldFileName As String, NewFileName As String, TriggerRestart As Boolean)
    End Sub

    ''' <summary>
    ''' 确保 PathTemp/Latest.exe 是最新正式版启动器，它会被用于整合包打包。
    ''' 如果不是，则下载一个。
    ''' </summary>
    Friend Sub DownloadLatestPCL(Optional LoaderToSyncProgress As LoaderBase = Nothing)
        '注意：如果要自行实现这个功能，请换用另一个文件路径，以免与官方版本冲突
    End Sub

#End Region

#Region "联网配置"

    ''' <summary>
    ''' 联网获取的配置信息。
    ''' 若获取失败或仍在获取中，可能为 Nothing。
    ''' </summary>
    Public ServerConfig As JObject

    Public ServerLoader As New LoaderTask(Of Integer, Integer)("Cosy Craft Launcher 配置更新", Sub() Logger.Info("该版本中不包含更新通知功能……"), Priority:=ThreadPriority.BelowNormal) With
        {.ReloadTimeout = 1000 * 60 * 60} '超时 1 小时

#End Region

#Region "赞助等级"

    Public ReadOnly Property CurrentRank As DonationRank
        Get
            Return DonationRank.None
        End Get
    End Property

    Public Sub InputPotatoCode(IsUpdating As Boolean)
    End Sub
    Friend Sub GeneratePotatoCode()
    End Sub

    ''' <summary>
    ''' 获取设备识别码。
    ''' </summary>
    Friend Function GetIdentify() As String
        Return "0000-0000-0000-0000"
    End Function

#End Region

End Module
