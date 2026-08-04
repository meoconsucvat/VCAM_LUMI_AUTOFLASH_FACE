from __future__ import annotations

import argparse
import datetime as _dt
import os
import select
import socket
import socketserver
import sys
import threading
import time
from pathlib import Path

import frida
import paramiko


JS = r"""
'use strict';

function now() {
  return (new Date()).toISOString();
}

function log(kind, obj) {
  try {
    send({ ts: now(), kind: kind, data: obj });
  } catch (e) {
    send({ ts: now(), kind: "log_error", data: String(e) });
  }
}

function redact(s) {
  if (s === null || s === undefined) return s;
  var out = String(s);
  out = out.replace(/("password"\s*:\s*)"[^"]*"/ig, '$1"<redacted>"');
  out = out.replace(/("token"\s*:\s*)"[^"]*"/ig, '$1"<redacted>"');
  out = out.replace(/("auth[^"]*"\s*:\s*)"[^"]*"/ig, '$1"<redacted>"');
  out = out.replace(/("signing_key"\s*:\s*)"[^"]*"/ig, '$1"<redacted>"');
  out = out.replace(/("key"\s*:\s*)"[^"]*"/ig, '$1"<redacted>"');
  out = out.replace(/(Authorization\s*=\s*)[^,}\n]+/ig, '$1<redacted>');
  return out;
}

function nsstr(obj) {
  try {
    if (obj === null || obj.isNull()) return null;
    return new ObjC.Object(obj).toString();
  } catch (e) {
    return "<obj:" + obj + ">";
  }
}

function nsdataToString(obj) {
  try {
    if (obj === null || obj.isNull()) return null;
    var data = new ObjC.Object(obj);
    var len = data.length().valueOf();
    if (len <= 0 || len > 16384) return "<NSData len=" + len + ">";
    var bytes = data.bytes();
    return Memory.readUtf8String(bytes, len);
  } catch (e) {
    return "<NSData decode failed: " + e + ">";
  }
}

function dictToString(obj) {
  try {
    if (obj === null || obj.isNull()) return null;
    return new ObjC.Object(obj).toString();
  } catch (e) {
    return "<dict:" + obj + ">";
  }
}

function tryHook(clsName, methodName, callbacks) {
  try {
    if (!ObjC.available) return false;
    var cls = ObjC.classes[clsName];
    if (!cls) {
      log("missing_class", clsName);
      return false;
    }
    var method = cls[methodName];
    if (!method) {
      log("missing_method", clsName + " " + methodName);
      return false;
    }
    Interceptor.attach(method.implementation, callbacks);
    log("hooked", clsName + " " + methodName);
    return true;
  } catch (e) {
    log("hook_error", clsName + " " + methodName + " :: " + e);
    return false;
  }
}

if (!ObjC.available) {
  log("fatal", "ObjC runtime unavailable in target");
} else {
  log("ready", "SpringBoard login capture loaded");

  tryHook("NSMutableURLRequest", "- setHTTPMethod:", {
    onEnter: function(args) {
      log("http_method", nsstr(args[2]));
    }
  });

  tryHook("NSMutableURLRequest", "- setValue:forHTTPHeaderField:", {
    onEnter: function(args) {
      var value = nsstr(args[2]);
      var field = nsstr(args[3]);
      if (field && /X-|Authorization|Content-Type|Vcam|Timestamp|Nonce|Signature/i.test(field)) {
        log("http_header", { field: field, value: redact(value) });
      }
    }
  });

  tryHook("NSMutableURLRequest", "- setHTTPBody:", {
    onEnter: function(args) {
      log("http_body", redact(nsdataToString(args[2])));
    }
  });

  tryHook("NSURLSession", "- dataTaskWithRequest:completionHandler:", {
    onEnter: function(args) {
      try {
        var req = new ObjC.Object(args[2]);
        var url = req.URL() ? req.URL().toString() : null;
        var method = req.HTTPMethod() ? req.HTTPMethod().toString() : null;
        var headers = req.allHTTPHeaderFields();
        var body = req.HTTPBody();
        log("data_task_request", {
          url: String(url),
          method: String(method),
          headers: redact(dictToString(headers)),
          body: redact(nsdataToString(body))
        });
      } catch (e) {
        log("data_task_request_error", String(e));
      }
    }
  });

  tryHook("NSURLSession", "- dataTaskWithRequest:", {
    onEnter: function(args) {
      try {
        var req = new ObjC.Object(args[2]);
        log("data_task_request_no_cb", {
          url: String(req.URL()),
          method: String(req.HTTPMethod()),
          headers: redact(dictToString(req.allHTTPHeaderFields())),
          body: redact(nsdataToString(req.HTTPBody()))
        });
      } catch (e) {
        log("data_task_request_no_cb_error", String(e));
      }
    }
  });

  tryHook("NSJSONSerialization", "+ JSONObjectWithData:options:error:", {
    onEnter: function(args) {
      this.body = redact(nsdataToString(args[2]));
    },
    onLeave: function(retval) {
      if (this.body) log("json_parse_input", this.body);
      if (!retval.isNull()) log("json_parse_output", redact(nsstr(retval)));
    }
  });

  tryHook("NSJSONSerialization", "+ dataWithJSONObject:options:error:", {
    onEnter: function(args) {
      log("json_serialize_object", redact(nsstr(args[2])));
    }
  });

  tryHook("NSUserDefaults", "- setObject:forKey:", {
    onEnter: function(args) {
      log("defaults_set", { key: nsstr(args[3]), value: redact(nsstr(args[2])) });
    }
  });

  tryHook("NSUserDefaults", "- objectForKey:", {
    onEnter: function(args) {
      this.key = nsstr(args[2]);
    },
    onLeave: function(retval) {
      if (this.key && /vcam|rtmp|token|auth|verify|login|key|url/i.test(this.key)) {
        log("defaults_get", { key: this.key, value: redact(nsstr(retval)) });
      }
    }
  });

  tryHook("UIAlertController", "+ alertControllerWithTitle:message:preferredStyle:", {
    onEnter: function(args) {
      log("alert_controller", { title: nsstr(args[2]), message: nsstr(args[3]) });
    }
  });

  tryHook("UIAlertView", "- initWithTitle:message:delegate:cancelButtonTitle:otherButtonTitles:", {
    onEnter: function(args) {
      log("alert_view", { title: nsstr(args[2]), message: nsstr(args[3]) });
    }
  });
}
"""


class ForwardServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(socketserver.BaseRequestHandler):
    ssh_transport: paramiko.Transport | None = None
    remote_host = "127.0.0.1"
    remote_port = 27042

    def handle(self) -> None:
        try:
            chan = self.ssh_transport.open_channel(
                "direct-tcpip",
                (self.remote_host, self.remote_port),
                self.request.getpeername(),
            )
        except Exception:
            return
        if chan is None:
            return
        try:
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
                chan.close()
            except Exception:
                pass
            try:
                self.request.close()
            except Exception:
                pass


def write_line(path: Path, line: str) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
        f.flush()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="192.168.2.120")
    ap.add_argument("--user", default="root")
    ap.add_argument("--password", default="123")
    ap.add_argument("--local-port", type=int, default=37042)
    ap.add_argument("--duration", type=int, default=900)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "springboard_login_frida.jsonl"
    status_path = out_dir / "springboard_login_capture.status.txt"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.host, username=args.user, password=args.password, timeout=12, banner_timeout=12, auth_timeout=12)

    Handler.ssh_transport = ssh.get_transport()
    server = ForwardServer(("127.0.0.1", args.local_port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    write_line(status_path, f"{_dt.datetime.now().isoformat()} tunnel_ready 127.0.0.1:{args.local_port}->iphone:27042")

    dm = frida.get_device_manager()
    device = dm.add_remote_device(f"127.0.0.1:{args.local_port}")
    session = device.attach("SpringBoard")

    def on_message(message, data):
        write_line(log_path, repr(message))
        if message.get("type") == "send":
            payload = message.get("payload")
            if isinstance(payload, dict) and payload.get("kind") in {"ready", "hooked", "fatal", "hook_error"}:
                write_line(status_path, f"{_dt.datetime.now().isoformat()} {payload}")

    script = session.create_script(JS)
    script.on("message", on_message)
    script.load()
    write_line(status_path, f"{_dt.datetime.now().isoformat()} frida_attached SpringBoard")
    print(f"READY status={status_path} log={log_path}", flush=True)

    end = time.time() + args.duration
    try:
        while time.time() < end:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        write_line(status_path, f"{_dt.datetime.now().isoformat()} stopping")
        try:
            session.detach()
        except Exception:
            pass
        server.shutdown()
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
