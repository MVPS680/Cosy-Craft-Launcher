Imports System.ComponentModel
Imports System.Windows.Media.Animation

' 双生主题的装饰背景。只改变背景颜色，避免正文与交互状态随动画闪动。
Public Class ScarletBackdrop
    Inherits Border

    Public Shared ReadOnly ModeProperty As DependencyProperty = DependencyProperty.Register(
        NameOf(Mode), GetType(String), GetType(ScarletBackdrop),
        New PropertyMetadata("Hero", AddressOf OnModeChanged))

    Public Property Mode As String
        Get
            Return CStr(GetValue(ModeProperty))
        End Get
        Set(value As String)
            SetValue(ModeProperty, value)
        End Set
    End Property

    Private Shared Event MotionChanged As EventHandler
    ' 所有页面共享时间基准，页面切换后接续同一段流光。
    Private Shared ReadOnly MotionTime As Diagnostics.Stopwatch = Diagnostics.Stopwatch.StartNew()
    Private OwnerWindow As Window
    Private Motion As Storyboard
    Private Attached As Boolean
    Private Running As Boolean

    Public Sub New()
        IsHitTestVisible = False
        Focusable = False
        Paint()
        AddHandler Loaded, AddressOf OnLoaded
        AddHandler Unloaded, AddressOf OnUnloaded
        AddHandler IsVisibleChanged, Sub() RefreshMotion()
    End Sub

    Public Shared Sub NotifyMotionChanged()
        RunInUi(Sub() RaiseEvent MotionChanged(Nothing, EventArgs.Empty))
    End Sub

    Private Shared Sub OnModeChanged(d As DependencyObject, e As DependencyPropertyChangedEventArgs)
        CType(d, ScarletBackdrop).Paint()
    End Sub

    Private Sub Paint()
        StopMotion()
        Dim StartColors As String()
        Dim EndColors As String()
        Select Case Mode
            Case "Title"
                StartColors = {"#43334F", "#62405C", "#83465F", "#995267"}
                EndColors = {"#74445D", "#80506E", "#624C78", "#453957"}
            Case "Ambient"
                StartColors = {"#EAE4F1", "#F2EDF5", "#F6EDF0", "#F5EDE5"}
                EndColors = {"#F2E8EE", "#F5EDF0", "#EDE7F3", "#E6ECF5"}
            Case "Ribbon"
                StartColors = {"#8175C8", "#BF88CA", "#D86279", "#D5A450"}
                EndColors = {"#CE8E58", "#D56F89", "#927DC9", "#708ABF"}
            Case Else
                StartColors = {"#F1EBF7", "#F6F1F8", "#FBF3F4", "#FBF5ED"}
                EndColors = {"#F7EEF3", "#FBF3EE", "#F3EDF8", "#EDF1FA"}
        End Select
        Dim Brush As New LinearGradientBrush With {.StartPoint = New Point(0, 0), .EndPoint = New Point(1, 0.6)}
        Motion = New Storyboard With {.RepeatBehavior = RepeatBehavior.Forever, .AutoReverse = True}
        Timeline.SetDesiredFrameRate(Motion, 24)
        For i = 0 To StartColors.Length - 1
            Dim StopColor As Color = ColorConverter.ConvertFromString(StartColors(i))
            Dim FinishColor As Color = ColorConverter.ConvertFromString(EndColors(i))
            Dim Gradient As New GradientStop(StopColor, i / CDbl(StartColors.Length - 1))
            Brush.GradientStops.Add(Gradient)
            Dim Animation As New ColorAnimation(StopColor, FinishColor, New Duration(TimeSpan.FromSeconds(14))) With {
                .EasingFunction = New SineEase With {.EasingMode = EasingMode.EaseInOut}}
            Storyboard.SetTarget(Animation, Me)
            Storyboard.SetTargetProperty(Animation, New PropertyPath(
                $"(0).(1)[{i}].(2)", Border.BackgroundProperty, LinearGradientBrush.GradientStopsProperty, GradientStop.ColorProperty))
            Motion.Children.Add(Animation)
        Next
        Background = Brush
        RefreshMotion()
    End Sub

    Private Sub OnLoaded(sender As Object, e As RoutedEventArgs)
        If Attached Then Return
        Attached = True
        OwnerWindow = Window.GetWindow(Me)
        AddHandler MotionChanged, AddressOf OnMotionChanged
        AddHandler SystemParameters.StaticPropertyChanged, AddressOf OnSystemChanged
        If OwnerWindow IsNot Nothing Then
            AddHandler OwnerWindow.StateChanged, AddressOf OnMotionChanged
            AddHandler OwnerWindow.IsVisibleChanged, AddressOf OnWindowVisibilityChanged
        End If
        RefreshMotion()
    End Sub

    Private Sub OnUnloaded(sender As Object, e As RoutedEventArgs)
        StopMotion()
        If Not Attached Then Return
        Attached = False
        RemoveHandler MotionChanged, AddressOf OnMotionChanged
        RemoveHandler SystemParameters.StaticPropertyChanged, AddressOf OnSystemChanged
        If OwnerWindow IsNot Nothing Then
            RemoveHandler OwnerWindow.StateChanged, AddressOf OnMotionChanged
            RemoveHandler OwnerWindow.IsVisibleChanged, AddressOf OnWindowVisibilityChanged
            OwnerWindow = Nothing
        End If
    End Sub

    Private Sub OnMotionChanged(sender As Object, e As EventArgs)
        RefreshMotion()
    End Sub

    Private Sub OnWindowVisibilityChanged(sender As Object, e As DependencyPropertyChangedEventArgs)
        RefreshMotion()
    End Sub

    Private Sub OnSystemChanged(sender As Object, e As PropertyChangedEventArgs)
        If e.PropertyName = NameOf(SystemParameters.ClientAreaAnimation) OrElse e.PropertyName = NameOf(SystemParameters.HighContrast) Then
            Dispatcher.InvokeAsync(Sub() RefreshMotion())
        End If
    End Sub

    Private Sub RefreshMotion()
        StopMotion()
        If Not Attached OrElse Not IsVisible OrElse OwnerWindow Is Nothing Then Return
        If Not OwnerWindow.IsVisible OrElse OwnerWindow.WindowState = WindowState.Minimized Then Return
        If Not SystemParameters.ClientAreaAnimation OrElse SystemParameters.HighContrast Then Return
        If Not Settings.Get(Of Boolean)("UiScarletMotion") Then Return
        Motion.Begin(Me, HandoffBehavior.SnapshotAndReplace, True)
        Motion.SeekAlignedToLastTick(Me, TimeSpan.FromSeconds(MotionTime.Elapsed.TotalSeconds Mod 28), TimeSeekOrigin.BeginTime)
        Running = True
    End Sub

    Private Sub StopMotion()
        If Not Running Then Return
        Motion.Remove(Me)
        Running = False
    End Sub
End Class
