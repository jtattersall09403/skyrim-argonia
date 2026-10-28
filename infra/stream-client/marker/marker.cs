// Argonia input marker (chunk 0.0 §c): the host half of the press-to-screen latency measurement.
// Polls XInput (slots 0-3, xinput1_4.dll) and the keyboard and mouse (GetAsyncKeyState) at ~1 kHz. On any new
// press it flashes a two-tone square in the top-left corner of the desktop: left half black and right half white,
// or the reverse, alternating per press, for FlashMs (default 60 ms, 3+ frames at 60 Hz). The window is topmost,
// click-through and never activates. The client page samples that corner of the decoded video and pairs each
// flash with the input it sent (src/marker_detect.ts). Each flash is also logged to
// C:\argonia\logs\marker\<utc date>.jsonl, and the geometry to C:\argonia\logs\marker\geometry.json (served to the
// page by the collector). Runs in the interactive Administrator session (scheduled task "argonia-input-marker", at
// logon). The game must be borderless windowed: an exclusive-fullscreen game hides every other window.
// Build (install.ps1): csc /target:winexe /r:System.Windows.Forms.dll /r:System.Drawing.dll marker.cs
// Args: [half-size px, default 24] [flash ms, default 60]
using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;

static class Native
{
    [StructLayout(LayoutKind.Sequential)]
    public struct XINPUT_GAMEPAD { public ushort wButtons; public byte bLeftTrigger; public byte bRightTrigger; public short sThumbLX; public short sThumbLY; public short sThumbRX; public short sThumbRY; }
    [StructLayout(LayoutKind.Sequential)]
    public struct XINPUT_STATE { public uint dwPacketNumber; public XINPUT_GAMEPAD Gamepad; }
    [DllImport("xinput1_4.dll")] public static extern uint XInputGetState(uint index, out XINPUT_STATE state);
    [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int vKey);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool SetLayeredWindowAttributes(IntPtr hwnd, uint key, byte alpha, uint flags);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hwnd, IntPtr after, int x, int y, int cx, int cy, uint flags);
    [DllImport("winmm.dll")] public static extern uint timeBeginPeriod(uint ms);
    public static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
    public const uint SWP_NOSIZE = 0x1, SWP_NOMOVE = 0x2, SWP_NOACTIVATE = 0x10, SWP_SHOWWINDOW = 0x40;
    public const uint LWA_ALPHA = 0x2;
}

class MarkerWindow : Form
{
    const int WS_EX_TOPMOST = 0x8, WS_EX_TRANSPARENT = 0x20, WS_EX_TOOLWINDOW = 0x80, WS_EX_LAYERED = 0x80000, WS_EX_NOACTIVATE = 0x08000000;
    public bool BlackLeft = true;
    readonly int half;

    public MarkerWindow(int half)
    {
        this.half = half;
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.Manual;
        Location = new Point(0, 0);
        ClientSize = new Size(half * 2, half);
        TopMost = true;
        DoubleBuffered = true;
        BackColor = Color.Black;
    }

    protected override CreateParams CreateParams
    {
        get
        {
            CreateParams cp = base.CreateParams;
            cp.ExStyle |= WS_EX_TOPMOST | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_LAYERED | WS_EX_NOACTIVATE;
            return cp;
        }
    }

    protected override bool ShowWithoutActivation { get { return true; } }

    protected override void OnHandleCreated(EventArgs e)
    {
        base.OnHandleCreated(e);
        Native.SetLayeredWindowAttributes(Handle, 0, 0, Native.LWA_ALPHA); // hidden until the first press
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.FillRectangle(BlackLeft ? Brushes.Black : Brushes.White, 0, 0, half, half);
        e.Graphics.FillRectangle(BlackLeft ? Brushes.White : Brushes.Black, half, 0, half, half);
    }

    public void Flash()
    {
        BlackLeft = !BlackLeft;
        Invalidate();
        Update();
        Native.SetWindowPos(Handle, Native.HWND_TOPMOST, 0, 0, 0, 0, Native.SWP_NOMOVE | Native.SWP_NOSIZE | Native.SWP_NOACTIVATE | Native.SWP_SHOWWINDOW);
        Native.SetLayeredWindowAttributes(Handle, 0, 255, Native.LWA_ALPHA);
    }

    public void Hide2() { Native.SetLayeredWindowAttributes(Handle, 0, 0, Native.LWA_ALPHA); }
}

static class Program
{
    static StreamWriter log;
    static string logDay;
    static readonly string Dir = @"C:\argonia\logs\marker";

    static void Log(string src, string code, bool blackLeft, double pollMs)
    {
        try
        {
            string day = DateTime.UtcNow.ToString("yyyy-MM-dd");
            if (log == null || day != logDay)
            {
                if (log != null) log.Dispose();
                log = new StreamWriter(Path.Combine(Dir, day + ".jsonl"), true, new UTF8Encoding(false));
                log.AutoFlush = true;
                logDay = day;
            }
            long ms = (long)(DateTime.UtcNow - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc)).TotalMilliseconds;
            log.WriteLine("{\"t\":" + ms + ",\"src\":\"" + src + "\",\"code\":\"" + code + "\",\"phase\":\"" + (blackLeft ? "BW" : "WB") + "\",\"pollMs\":" + pollMs.ToString("0.00", System.Globalization.CultureInfo.InvariantCulture) + "}");
        }
        catch (Exception) { }
    }

    static void WriteGeometry(int half, int flashMs)
    {
        try
        {
            Rectangle b = Screen.PrimaryScreen.Bounds;
            File.WriteAllText(Path.Combine(Dir, "geometry.json"),
                "{\"screenWidth\":" + b.Width + ",\"screenHeight\":" + b.Height + ",\"half\":" + half + ",\"flashMs\":" + flashMs + ",\"x\":0,\"y\":0}");
        }
        catch (Exception) { }
    }

    [STAThread]
    static void Main(string[] args)
    {
        bool created;
        using (Mutex m = new Mutex(true, @"Local\argonia-input-marker", out created))
        {
            if (!created) return;
            int half = args.Length > 0 ? int.Parse(args[0]) : 24;
            int flashMs = args.Length > 1 ? int.Parse(args[1]) : 60;
            Native.SetProcessDPIAware();
            Native.timeBeginPeriod(1);
            Directory.CreateDirectory(Dir);
            WriteGeometry(half, flashMs);
            // DCV and Sunshine resize the console desktop to their clients: keep the page's sample points true
            Microsoft.Win32.SystemEvents.DisplaySettingsChanged += delegate { WriteGeometry(half, flashMs); };

            MarkerWindow w = new MarkerWindow(half);
            w.Show();
            long hideAt = long.MaxValue;
            Stopwatch clock = Stopwatch.StartNew();
            System.Windows.Forms.Timer hider = new System.Windows.Forms.Timer();
            hider.Interval = 5;
            hider.Tick += delegate { if (clock.ElapsedMilliseconds >= Interlocked.Read(ref hideAt)) { Interlocked.Exchange(ref hideAt, long.MaxValue); w.Hide2(); } };
            hider.Start();

            Thread poll = new Thread(delegate ()
            {
                ushort[] prevPad = new ushort[4];
                bool[] prevKey = new bool[256];
                double last = clock.Elapsed.TotalMilliseconds;
                while (true)
                {
                    double now = clock.Elapsed.TotalMilliseconds;
                    double pollMs = now - last;
                    last = now;
                    string src = null, code = null;
                    for (uint i = 0; i < 4; i++)
                    {
                        Native.XINPUT_STATE s;
                        ushort bits = 0;
                        if (Native.XInputGetState(i, out s) == 0)
                        {
                            bits = s.Gamepad.wButtons;
                            if (s.Gamepad.bLeftTrigger > 128) bits |= 0x0400;  // 0x0400 and 0x0800 are unused XInput bits
                            if (s.Gamepad.bRightTrigger > 128) bits |= 0x0800;
                        }
                        ushort fresh = (ushort)(bits & ~prevPad[i]);
                        if (fresh != 0 && src == null) { src = "xinput" + i; code = "0x" + fresh.ToString("x4"); }
                        prevPad[i] = bits;
                    }
                    for (int vk = 1; vk < 255; vk++)
                    {
                        bool down = (Native.GetAsyncKeyState(vk) & 0x8000) != 0;
                        if (down && !prevKey[vk] && src == null) { src = vk <= 6 && vk != 3 ? "mouse" : "key"; code = "vk" + vk; }
                        prevKey[vk] = down;
                    }
                    if (src != null)
                    {
                        string s2 = src, c2 = code; double p2 = pollMs;
                        w.BeginInvoke((MethodInvoker)delegate
                        {
                            w.Flash();
                            Interlocked.Exchange(ref hideAt, clock.ElapsedMilliseconds + flashMs);
                            Log(s2, c2, w.BlackLeft, p2);
                        });
                    }
                    Thread.Sleep(1);
                }
            });
            poll.IsBackground = true;
            poll.Priority = ThreadPriority.AboveNormal;
            poll.Start();
            Application.Run(w);
        }
    }
}
