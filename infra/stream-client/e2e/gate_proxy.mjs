// A stand-in for the sign-in gate's routing (chunk 0.0 §c), for the end-to-end check only: one origin that sends
// /argonia-metrics* to the collector and everything else (WebSocket upgrades included) to Moonlight-Web. The real
// gate must route the same way.  Usage: startGate({ port, web: 18081, collector: 18091 }) -> server
import http from "node:http"
import net from "node:net"

export function startGate({ port, web, collector }) {
    const target = (url) => (/(^|\/)argonia-metrics(\/|$|\?)/.test(url) ? collector : web)
    const server = http.createServer((req, res) => {
        const up = http.request({ host: "127.0.0.1", port: target(req.url), path: req.url, method: req.method, headers: req.headers }, (r) => {
            res.writeHead(r.statusCode, r.headers)
            r.pipe(res)
        })
        up.on("error", (e) => { res.writeHead(502); res.end(String(e)) })
        req.pipe(up)
    })
    server.on("upgrade", (req, socket, head) => {
        const up = net.connect(target(req.url), "127.0.0.1", () => {
            const lines = [`${req.method} ${req.url} HTTP/1.1`, ...Object.entries(req.headers).map(([k, v]) => `${k}: ${v}`), "", ""]
            up.write(lines.join("\r\n"))
            if (head?.length) up.write(head)
            up.pipe(socket)
            socket.pipe(up)
        })
        up.on("error", () => socket.destroy())
        socket.on("error", () => up.destroy())
    })
    return new Promise((resolve) => server.listen(port, "127.0.0.1", () => resolve(server)))
}
