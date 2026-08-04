from __future__ import annotations

import argparse
import datetime as dt
import json
import select
import socketserver
import threading
import time
from pathlib import Path

import frida
import paramiko


JS = r"""
'use strict';

function sendlog(kind, data) {
  try { send({ts: (new Date()).toISOString(), kind: kind, data: data}); }
  catch (e) { send({ts: (new Date()).toISOString(), kind: 'send_error', data: String(e)}); }
}

function readUtf8(ptr, len) {
  try {
    if (ptr.isNull() || len <= 0 || len > 32768) return null;
    return Memory.readUtf8String(ptr, len);
  } catch (e) {
    return null;
  }
}

function readHex(ptr, len) {
  try {
    if (ptr.isNull() || len <= 0 || len > 4096) return null;
    var b = Memory.readByteArray(ptr, len);
    return Array.prototype.map.call(new Uint8Array(b), function(x) {
      return ('0' + x.toString(16)).slice(-2);
    }).join('');
  } catch (e) {
    return null;
  }
}

function nsstr(obj) {
  try {
    if (obj === null || obj.isNull()) return null;
    return new ObjC.Object(obj).toString();
  } catch (e) { return '<obj:' + obj + '>'; }
}

function nsdataToString(obj) {
  try {
    if (obj === null || obj.isNull()) return null;
    var data = new ObjC.Object(obj);
    var len = data.length().valueOf();
    if (len <= 0 || len > 32768) return '<NSData len=' + len + '>';
    return Memory.readUtf8String(data.bytes(), len);
  } catch (e) { return '<NSData decode failed: ' + e + '>'; }
}

function dictToString(obj) {
  try {
    if (obj === null || obj.isNull()) return null;
    return new ObjC.Object(obj).toString();
  } catch (e) { return '<dict:' + obj + '>'; }
}

function hookObjC(clsName, methName, callbacks) {
  try {
    if (!ObjC.available) return false;
    var cls = ObjC.classes[clsName];
    if (!cls || !cls[methName]) {
      sendlog('missing_objc', clsName + ' ' + methName);
      return false;
    }
    Interceptor.attach(cls[methName].implementation, callbacks);
    sendlog('hooked_objc', clsName + ' ' + methName);
    return true;
  } catch (e) {
    sendlog('hook_objc_error', clsName + ' ' + methName + ' :: ' + e);
    return false;
  }
}

sendlog('ready', 'SpringBoard HMAC capture loaded');

var cchmac = Module.findExportByName(null, 'CCHmac');
if (cchmac) {
  Interceptor.attach(cchmac, {
    onEnter: function(args) {
      var alg = args[0].toInt32();
      var keyLen = args[2].toInt32();
      var dataLen = args[4].toInt32();
      var msg = readUtf8(args[3], dataLen);
      if (alg === 2 || (msg && msg.indexOf('v3:') >= 0)) {
        this.capture = true;
        this.outPtr = args[5];
        this.keyLen = keyLen;
        this.dataLen = dataLen;
        sendlog('CCHmac_enter', {
          alg: alg,
          key_len: keyLen,
          key_utf8: readUtf8(args[1], keyLen),
          key_hex: readHex(args[1], keyLen),
          data_len: dataLen,
          data_utf8: msg,
          data_hex: readHex(args[3], dataLen)
        });
      }
    },
    onLeave: function(retval) {
      if (this.capture) {
        sendlog('CCHmac_leave', { mac_hex: readHex(this.outPtr, 32) });
      }
    }
  });
  sendlog('hooked_c', 'CCHmac');
} else {
  sendlog('missing_c', 'CCHmac');
}

hookObjC('NSMutableURLRequest', '- setValue:forHTTPHeaderField:', {
  onEnter: function(args) {
    var value = nsstr(args[2]);
    var field = nsstr(args[3]);
    if (field && /X-|Authorization|Content-Type|Vcam|Timestamp|Nonce|Signature/i.test(field)) {
      sendlog('http_header', { field: field, value: value });
    }
  }
});

hookObjC('NSMutableURLRequest', '- setHTTPBody:', {
  onEnter: function(args) {
    sendlog('http_body', nsdataToString(args[2]));
  }
});

hookObjC('NSURLSession', '- dataTaskWithRequest:completionHandler:', {
  onEnter: function(args) {
    try {
      var req = new ObjC.Object(args[2]);
      sendlog('data_task_request', {
        url: String(req.URL()),
        method: String(req.HTTPMethod()),
        headers: dictToString(req.allHTTPHeaderFields()),
        body: nsdataToString(req.HTTPBody())
      });
    } catch (e) {
      sendlog('data_task_error', String(e));
    }
  }
});

hookObjC('UIAlertController', '+ alertControllerWithTitle:message:preferredStyle:', {
  onEnter: function(args) {
    sendlog('alert', { title: nsstr(args[2]), message: nsstr(args[3]) });
  }
});
"""


class ForwardServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(socketserver.BaseRequestHandler):
    ssh_transport: paramiko.Transport | None = None
    remote_host = "127.0.0.1"
    remote_port = 27042

    def handle(self) -> None:
        chan = None
        try:
            chan = self.ssh_transport.open_channel(
                "direct-tcpip", (self.remote_host, self.remote_port), self.request.getpeername()
            )
            while True:
                r, _, _ = select.select([self.request, chan], [], [])
                if self.request in r:
                    data = self.request.recv(16384)
                    if not data:
                        break
                    chan.sendall(data)
                if chan in r:
                    data = chan.recv(16384)
                    if not data:
                        break
                    self.request.sendall(data)
        finally:
            try:
                if chan:
                    chan.close()
            except Exception:
                pass
            try:
                self.request.close()
            except Exception:
                pass


def append_jsonl(path: Path, obj: object) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="192.168.2.120")
    ap.add_argument("--user", default="root")
    ap.add_argument("--password", default="123")
    ap.add_argument("--local-port", type=int, default=37043)
    ap.add_argument("--duration", type=int, default=180)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / "springboard_hmac_capture.jsonl"
    status_path = out / "springboard_hmac_capture.status.txt"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        args.host,
        username=args.user,
        password=args.password,
        timeout=12,
        banner_timeout=12,
        auth_timeout=12,
        look_for_keys=False,
        allow_agent=False,
    )

    Handler.ssh_transport = ssh.get_transport()
    server = ForwardServer(("127.0.0.1", args.local_port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    dm = frida.get_device_manager()
    device = dm.add_remote_device(f"127.0.0.1:{args.local_port}")
    session = device.attach("SpringBoard")

    def on_message(message, data):
        append_jsonl(log_path, message)
        payload = message.get("payload")
        if isinstance(payload, dict) and payload.get("kind") in {
            "ready",
            "hooked_c",
            "hooked_objc",
            "missing_c",
            "missing_objc",
            "hook_objc_error",
        }:
            with status_path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(f"{dt.datetime.now().isoformat()} {payload}\n")

    script = session.create_script(JS)
    script.on("message", on_message)
    script.load()
    print(f"READY log={log_path}", flush=True)

    try:
        end = time.time() + args.duration
        while time.time() < end:
            time.sleep(1)
    finally:
        try:
            session.detach()
        except Exception:
            pass
        server.shutdown()
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
