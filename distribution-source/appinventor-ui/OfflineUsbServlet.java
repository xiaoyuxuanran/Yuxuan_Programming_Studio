package com.google.appinventor.server;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import javax.servlet.http.*;
import org.json.JSONObject;

/** Same-origin, authenticated bridge to the managed desktop ADB service. */
public final class OfflineUsbServlet extends HttpServlet {
  private static final Set<String> GET_PATHS = Set.of("/devices", "/job", "/logcat");
  private static boolean allowed(HttpServletRequest req) {
    String remote = req.getRemoteAddr();
    if (!("127.0.0.1".equals(remote) || "::1".equals(remote)
        || "0:0:0:0:0:0:0:1".equals(remote))) return false;
    if (!("127.0.0.1".equals(req.getServerName()) || "localhost".equals(req.getServerName()))) return false;
    if (!"1".equals(req.getHeader("X-Offline-Usb"))) return false;
    String origin = req.getHeader("Origin");
    String expected = "http://" + req.getServerName() + ":" + req.getServerPort();
    return origin == null || expected.equals(origin);
  }
  @Override protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {
    forward(req, resp, false);
  }
  @Override protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
    forward(req, resp, true);
  }
  private void forward(HttpServletRequest req, HttpServletResponse resp, boolean post) throws IOException {
    resp.setCharacterEncoding("UTF-8");
    resp.setContentType("application/json;charset=UTF-8");
    resp.setHeader("Cache-Control", "no-store");
    resp.setHeader("X-Content-Type-Options", "nosniff");
    if (!allowed(req)) { resp.sendError(403); return; }
    String path = req.getPathInfo();
    if (post ? !"/install".equals(path) : !GET_PATHS.contains(path)) { resp.sendError(404); return; }
    String query = req.getQueryString();
    if (query != null && query.length() > 1024) { resp.sendError(400); return; }
    byte[] body = null;
    if (post) {
      if (req.getContentType() == null || !req.getContentType().startsWith("application/json")) {
        resp.sendError(415); return;
      }
      byte[] incoming = req.getInputStream().readNBytes(4097);
      if (incoming.length > 4096) { resp.sendError(413); return; }
      try {
        JSONObject json = new JSONObject(new String(incoming, StandardCharsets.UTF_8));
        String cookie = "";
        if (req.getCookies() != null) for (Cookie c : req.getCookies())
          if ("AppInventor".equals(c.getName())) cookie = "AppInventor=" + c.getValue();
        json.put("cookie", cookie);
        body = json.toString().getBytes(StandardCharsets.UTF_8);
      } catch (Exception e) { resp.sendError(400); return; }
    }
    HttpURLConnection connection = null;
    try {
      int port = Integer.parseInt(System.getProperty("offline.usb.port"));
      URL address = new URL("http://127.0.0.1:" + port + "/api" + path
          + (query == null ? "" : "?" + query));
      connection = (HttpURLConnection) address.openConnection(Proxy.NO_PROXY);
      connection.setConnectTimeout(3000);
      connection.setReadTimeout(30000);
      connection.setInstanceFollowRedirects(false);
      connection.setRequestProperty("X-Offline-Control", System.getProperty("offline.control.token"));
      connection.setRequestProperty("Origin", "http://127.0.0.1:" + req.getServerPort());
      if (post) {
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setDoOutput(true);
        connection.setFixedLengthStreamingMode(body.length);
        try (OutputStream out = connection.getOutputStream()) { out.write(body); }
      }
      int code = connection.getResponseCode();
      resp.setStatus(code);
      InputStream input = code < 400 ? connection.getInputStream() : connection.getErrorStream();
      if (input != null) try (InputStream in = input) { in.transferTo(resp.getOutputStream()); }
    } catch (Exception e) {
      getServletContext().log("USB bridge failed", e);
      resp.setStatus(503);
      resp.getWriter().print("{\"error\":\"USB 调试服务暂时不可用，请重新启动 App Inventor。\"}");
    } finally { if (connection != null) connection.disconnect(); }
  }
}
