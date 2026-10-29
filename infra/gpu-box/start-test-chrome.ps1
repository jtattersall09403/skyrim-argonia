# The agents' test browser on the game machine (chunk 0.0 §c): Google Chrome, headless, in the desktop session so it
# decodes video on the T4 (H.264 and H.265 in hardware, as the owner's phone does), with its DevTools port on
# localhost only; drive.mjs with ARGONIA_BROWSER=box drives it through SSH. Headless: no window, so it never takes
# the desktop or the keyboard from Skyrim. Run with run.sh desktop.
Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'argonia-chrome' } | % { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }
Start-Process 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--headless=new', '--remote-debugging-port=9222',
  '--remote-debugging-address=127.0.0.1', '--user-data-dir=C:\argonia\argonia-chrome', '--use-angle=d3d11', '--enable-gpu',
  '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required', '--no-first-run', 'about:blank'
Start-Sleep 4
(ConvertFrom-Json (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:9222/json/version).Content).Browser
