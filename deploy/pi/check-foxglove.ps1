param([string]$Url = 'ws://192.168.20.20:8765', [string]$Topic = '/camera/image_raw/compressed')
$ErrorActionPreference = 'Stop'
$socket = [System.Net.WebSockets.ClientWebSocket]::new()
$socket.Options.AddSubProtocol('foxglove.websocket.v1')
$socket.Options.AddSubProtocol('foxglove.sdk.v1')
$socket.Options.Proxy = $null
$deadline = [System.Threading.CancellationTokenSource]::new(20000)
try {
    $null = $socket.ConnectAsync([Uri]$Url, $deadline.Token).GetAwaiter().GetResult()
    $buffer = [byte[]]::new(1048576)
    $channels = @()
    while ($channels.Count -eq 0) {
        $stream = [System.IO.MemoryStream]::new()
        do {
            $result = $socket.ReceiveAsync([ArraySegment[byte]]::new($buffer), $deadline.Token).GetAwaiter().GetResult()
            $stream.Write($buffer, 0, $result.Count)
        } while (-not $result.EndOfMessage)
        $message = [Text.Encoding]::UTF8.GetString($stream.ToArray()) | ConvertFrom-Json
        $stream.Dispose()
        if ($message.op -eq 'advertise') { $channels = @($message.channels | Where-Object topic -eq $Topic) }
    }
    $subscription = @{op='subscribe'; subscriptions=@(@{id=1; channelId=$channels[0].id})} | ConvertTo-Json -Depth 4 -Compress
    $payload = [Text.Encoding]::UTF8.GetBytes($subscription)
    $null = $socket.SendAsync([ArraySegment[byte]]::new($payload), [System.Net.WebSockets.WebSocketMessageType]::Text, $true, $deadline.Token).GetAwaiter().GetResult()
    do {
        $bytes = 0
        do {
            $result = $socket.ReceiveAsync([ArraySegment[byte]]::new($buffer), $deadline.Token).GetAwaiter().GetResult()
            $bytes += $result.Count
        } while (-not $result.EndOfMessage)
    } while ($result.MessageType -ne [System.Net.WebSockets.WebSocketMessageType]::Binary)
    Write-Output "Received compressed camera data from $Url ($bytes bytes)."
} finally {
    $socket.Abort()
    $socket.Dispose()
    $deadline.Dispose()
}
