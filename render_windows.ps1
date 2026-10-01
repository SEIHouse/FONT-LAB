param([Parameter(Mandatory=$true)][string]$Layout,
      [Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore, PresentationFramework, WindowsBase
$proof = Get-Content -LiteralPath $Layout -Raw -Encoding UTF8 | ConvertFrom-Json
$dpi = [double]$proof.dpi
$width = 1240
$height = 1510
$glyphFaces = @{}

function Brush([string]$Color) {
    return [System.Windows.Media.BrushConverter]::new().ConvertFromString($Color)
}
function Label($Context, [double]$X, [double]$Y, [string]$Text, [double]$Size, $Ink) {
    $label = [System.Windows.Media.FormattedText]::new($Text,
        [System.Globalization.CultureInfo]::InvariantCulture, [System.Windows.FlowDirection]::LeftToRight,
        [System.Windows.Media.Typeface]::new('Segoe UI'), $Size, $Ink, $dpi/96)
    $Context.DrawText($label, [System.Windows.Point]::new($X, $Y))
}
foreach ($theme in @('day', 'night')) {
    $bg = Brush $(if ($theme -eq 'day') {'#FAF7F0'} else {'#14131A'})
    $panel = Brush $(if ($theme -eq 'day') {'#FFFDF8'} else {'#1D1B24'})
    $ink = Brush $(if ($theme -eq 'day') {'#29252B'} else {'#E8E3DB'})
    $muted = Brush $(if ($theme -eq 'day') {'#64596B'} else {'#B6AFC4'})
    $visual = [System.Windows.Media.DrawingVisual]::new()
    [System.Windows.Media.TextOptions]::SetTextRenderingMode($visual, [System.Windows.Media.TextRenderingMode]::Grayscale)
    $dc = $visual.RenderOpen()
    $dc.DrawRectangle($bg, $null, [System.Windows.Rect]::new(0, 0, $width, $height))
    Label $dc 24 12 "SEIReader $($proof.candidate) / $($proof.baseline) - small text" 24 $ink
    Label $dc 24 48 "Windows WPF grayscale, HarfBuzz shaping, $dpi dpi. Native sizes; browser/device results separate." 14 $muted
    Label $dc 24 80 "Candidate $($proof.candidate)" 18 $ink
    Label $dc 642 80 "Baseline $($proof.baseline)" 18 $ink
    $y = 118
    foreach ($row in $proof.rows) {
        $column = 0
        foreach ($face in $row.faces) {
            $x = 24 + 618*$column
            $dc.DrawRectangle($panel, $null, [System.Windows.Rect]::new($x, $y, 572, 148))
            Label $dc ($x+12) ($y+7) "$($row.weight) / $($row.size)px" 13 $muted
            $baseline = $y+46
            foreach ($line in $face.lines) {
                if (-not $glyphFaces.ContainsKey($line.path)) {
                    $glyphFaces[$line.path] = [System.Windows.Media.GlyphTypeface]::new([uri]$line.path)
                }
                $ids = [System.Collections.Generic.List[uint16]]::new()
                $advances = [System.Collections.Generic.List[double]]::new()
                $offsets = [System.Collections.Generic.List[System.Windows.Point]]::new()
                foreach ($id in $line.glyphs) { $ids.Add([uint16]$id) }
                foreach ($advance in $line.advances) { $advances.Add([double]$advance) }
                foreach ($offset in $line.offsets) { $offsets.Add([System.Windows.Point]::new($offset[0], $offset[1])) }
                $run = [System.Windows.Media.GlyphRun]::new($glyphFaces[$line.path], 0, $false,
                    [double]$row.size, [single]($dpi/96), $ids, [System.Windows.Point]::new($x+12, $baseline),
                    $advances, $offsets, $null, $null, $null, $null,
                    [System.Windows.Markup.XmlLanguage]::GetLanguage('en'))
                $dc.DrawGlyphRun($ink, $run)
                $baseline += 21
            }
            $column++
        }
        $y += 154
    }
    $dc.Close()
    $bitmap = [System.Windows.Media.Imaging.RenderTargetBitmap]::new(
        [int]($width*$dpi/96), [int]($height*$dpi/96), $dpi, $dpi, [System.Windows.Media.PixelFormats]::Pbgra32)
    $bitmap.Render($visual)
    $encoder = [System.Windows.Media.Imaging.PngBitmapEncoder]::new()
    $encoder.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($bitmap))
    $path = Join-Path $OutputDirectory "windows-$theme-$dpi.png"
    $stream = [System.IO.File]::Create($path)
    try { $encoder.Save($stream) } finally { $stream.Dispose() }
    Write-Output $path
}
