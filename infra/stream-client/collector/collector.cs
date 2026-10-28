// Argonia stream-metrics collector (chunk 0.0 §c). Listens on http://127.0.0.1:8091/ (local only: the sign-in gate
// routes the page's same-origin path /argonia-metrics here) and appends the client page's JSON lines to
// C:\argonia\logs\stream-metrics\<utc date>.jsonl, each stamped with the receive time ("rx", UTC ms).
//   POST .../argonia-metrics          body: JSON lines (text/plain; also what sendBeacon sends)  -> 204
//   GET  .../argonia-metrics/marker   the input marker's geometry.json (the page's sample points)
//   GET  .../argonia-metrics/health   {"ok":true,...}
// Any path prefix before /argonia-metrics is accepted, so the gate may forward the path unchanged.
// Run at boot by the scheduled task "argonia-stream-collector" (install.ps1). Build: csc collector.cs
using System;
using System.IO;
using System.Net;
using System.Text;

static class Collector
{
    const string Root = @"C:\argonia\logs\stream-metrics";
    const string Geometry = @"C:\argonia\logs\marker\geometry.json";
    const int MaxBody = 4 * 1024 * 1024;
    const int MaxLine = 64 * 1024;
    static long lines;

    static void Main(string[] args)
    {
        string prefix = args.Length > 0 ? args[0] : "http://127.0.0.1:8091/";
        Directory.CreateDirectory(Root);
        HttpListener http = new HttpListener();
        http.Prefixes.Add(prefix);
        http.Start();
        Console.WriteLine("argonia collector on " + prefix + " writing " + Root);
        while (true)
        {
            HttpListenerContext ctx;
            try { ctx = http.GetContext(); } catch (Exception e) { Console.Error.WriteLine(e.Message); continue; }
            try { Handle(ctx); }
            catch (Exception e)
            {
                Console.Error.WriteLine(DateTime.UtcNow.ToString("o") + " " + e.Message);
                try { ctx.Response.StatusCode = 500; ctx.Response.Close(); } catch (Exception) { }
            }
        }
    }

    static void Reply(HttpListenerResponse r, int status, string type, string body)
    {
        r.StatusCode = status;
        r.Headers["Access-Control-Allow-Origin"] = "*";
        r.Headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS";
        r.Headers["Access-Control-Allow-Headers"] = "Content-Type";
        r.Headers["Cache-Control"] = "no-store";
        if (body != null)
        {
            byte[] b = Encoding.UTF8.GetBytes(body);
            r.ContentType = type;
            r.ContentLength64 = b.Length;
            r.OutputStream.Write(b, 0, b.Length);
        }
        r.Close();
    }

    static void Handle(HttpListenerContext ctx)
    {
        HttpListenerRequest q = ctx.Request;
        string path = q.Url.AbsolutePath.TrimEnd('/');
        int at = path.IndexOf("/argonia-metrics", StringComparison.Ordinal);
        string sub = at < 0 ? null : path.Substring(at + "/argonia-metrics".Length);
        if (sub == null) { Reply(ctx.Response, 404, "text/plain", "not found"); return; }
        if (q.HttpMethod == "OPTIONS") { Reply(ctx.Response, 204, null, null); return; }
        if (q.HttpMethod == "GET" && sub == "/health")
        {
            Reply(ctx.Response, 200, "application/json", "{\"ok\":true,\"lines\":" + lines + ",\"utc\":\"" + DateTime.UtcNow.ToString("o") + "\"}");
            return;
        }
        if (q.HttpMethod == "GET" && sub == "/marker")
        {
            if (File.Exists(Geometry)) Reply(ctx.Response, 200, "application/json", File.ReadAllText(Geometry));
            else Reply(ctx.Response, 404, "application/json", "{}");
            return;
        }
        if (q.HttpMethod != "POST" || sub != "") { Reply(ctx.Response, 405, "text/plain", "method"); return; }

        string body;
        using (MemoryStream ms = new MemoryStream())
        {
            byte[] buf = new byte[65536];
            int n;
            while ((n = q.InputStream.Read(buf, 0, buf.Length)) > 0)
            {
                ms.Write(buf, 0, n);
                if (ms.Length > MaxBody) { Reply(ctx.Response, 413, "text/plain", "too large"); return; }
            }
            body = Encoding.UTF8.GetString(ms.ToArray());
        }
        long rx = (long)(DateTime.UtcNow - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc)).TotalMilliseconds;
        StringBuilder outp = new StringBuilder();
        int kept = 0;
        foreach (string raw in body.Split('\n'))
        {
            string line = raw.Trim();
            // a record is one JSON object; anything else is dropped (no parser here: shape checks only)
            if (line.Length < 3 || line.Length > MaxLine || line[0] != '{' || line[line.Length - 1] != '}') continue;
            outp.Append("{\"rx\":").Append(rx).Append(',').Append(line, 1, line.Length - 1).Append('\n');
            kept++;
        }
        if (kept > 0)
        {
            string file = Path.Combine(Root, DateTime.UtcNow.ToString("yyyy-MM-dd") + ".jsonl");
            File.AppendAllText(file, outp.ToString(), new UTF8Encoding(false));
            lines += kept;
        }
        Reply(ctx.Response, 204, null, null);
    }
}
