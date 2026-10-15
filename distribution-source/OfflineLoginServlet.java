package com.google.appinventor.server;

import com.google.appinventor.server.storage.StorageIo;
import com.google.appinventor.server.storage.StorageIoInstanceHolder;
import com.google.appinventor.shared.rpc.user.User;
import com.google.apphosting.api.ApiProxy;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.util.*;


import javax.servlet.http.*;
import org.json.JSONObject;

/** Local-account adapter for the Windows desktop distribution. */
public final class OfflineLoginServlet extends HttpServlet {
  private static final Object ACCOUNT_LOCK = new Object();
  private static final SecureRandom RANDOM = new SecureRandom();
  private final StorageIo storage = StorageIoInstanceHolder.getInstance();
  /** Apply the release default once, retaining subsequent explicit UI choices. */
  public static void ensureClassicLayout(String userId) throws IOException {
    synchronized(ACCOUNT_LOCK) {
      Path marker=Paths.get(System.getProperty("offline.data"),"config","classic-layout-v1");
      if(Files.isRegularFile(marker) && Files.readString(marker).equals(userId))return;
      try {
        StorageIo io=StorageIoInstanceHolder.getInstance();
        String saved=io.loadSettings(userId);
        JSONObject settings=saved==null || saved.trim().isEmpty()?new JSONObject():new JSONObject(saved);
        JSONObject general=settings.optJSONObject("GeneralSettings");
        if(general==null){general=new JSONObject();settings.put("GeneralSettings",general);}
        general.put("NewLayout","false");
        general.put("ShowUIPicker","False");
        io.storeSettings(userId,settings.toString());
        Files.createDirectories(marker.getParent());
        Files.writeString(marker,userId);
      } catch(Exception e){throw new IOException("Cannot set the default classic layout",e);}
    }
  }
  private Path accountPath() { return Paths.get(System.getProperty("offline.data"), "config", "account.properties"); }
  private Properties account() throws IOException {
    Properties p = new Properties();
    if (Files.isRegularFile(accountPath())) try (InputStream in = Files.newInputStream(accountPath())) { p.load(in); }
    return p;
  }
  private static String token() { byte[] b=new byte[24]; RANDOM.nextBytes(b); return Base64.getUrlEncoder().withoutPadding().encodeToString(b); }
  private static boolean eq(String a,String b) { return a!=null && b!=null && MessageDigest.isEqual(a.getBytes(StandardCharsets.UTF_8),b.getBytes(StandardCharsets.UTF_8)); }
  private static String escape(String s) { return s.replace("&","&amp;").replace("<","&lt;").replace("\"","&quot;"); }
  private boolean local(HttpServletRequest req) { return "127.0.0.1".equals(req.getRemoteAddr()) || "0:0:0:0:0:0:0:1".equals(req.getRemoteAddr()) || "::1".equals(req.getRemoteAddr()); }
  private void headers(HttpServletResponse resp) {
    resp.setCharacterEncoding("UTF-8"); resp.setContentType("text/html;charset=UTF-8");
    resp.setHeader("Cache-Control","no-store"); resp.setHeader("X-Frame-Options","DENY");
    resp.setHeader("Content-Security-Policy","default-src 'none'; style-src 'unsafe-inline'; img-src 'self'; form-action 'self'; frame-ancestors 'none'");
  }
  @Override protected void doGet(HttpServletRequest req,HttpServletResponse resp) throws IOException {
    if(!local(req)){resp.sendError(403);return;}
    if(req.getRequestURI().endsWith("/_health")){resp.setContentType("text/plain");resp.getWriter().print("AppInventorOffline/1");return;}
    if(req.getRequestURI().contains("/google") || req.getRequestURI().contains("/sendlink")){resp.sendError(404);return;}
    render(req,resp,"");
  }
  private void render(HttpServletRequest req,HttpServletResponse resp,String error) throws IOException {
    headers(resp);
    HttpSession session=req.getSession(true); String csrf=(String)session.getAttribute("offline.csrf");
    if(csrf==null){csrf=token();session.setAttribute("offline.csrf",csrf);}
    PrintWriter out=resp.getWriter();
    out.print("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><link rel='icon' href='/favicon.ico?v=sky2'><title>羽轩 · App Inventor</title><style>body{margin:0;background:linear-gradient(135deg,#eff9ff,#fff 60%,#dff3ff);color:#12344a;font:16px 'Segoe UI','Microsoft YaHei',sans-serif;display:grid;place-items:center;min-height:100vh}.card{background:white;width:min(410px,82vw);padding:36px;border:1px solid #c7e7f7;border-radius:22px;box-shadow:0 18px 65px #0284c718}.logo{display:block;width:116px;height:116px;object-fit:contain;margin:0 auto 20px;border-radius:50%}h1{font-size:27px;margin:10px 0 12px}.brand{font-weight:bold;color:#0284c7;font-size:14px;letter-spacing:1px}p{line-height:1.7;color:#507084}label{display:block;margin:22px 0 8px}input{width:100%;box-sizing:border-box;padding:13px;border:1px solid #b5daee;border-radius:9px;font:inherit}input:focus{outline:3px solid #bae6fd;border-color:#0284c7}button{width:100%;margin-top:22px;background:#0284c7;color:white;border:0;border-radius:9px;padding:14px;font:inherit;font-weight:600;cursor:pointer}button:hover{background:#0369a1}.error{color:#b42318}.hint{font-size:13px;margin-bottom:0}</style><main class='card'><img class='logo' src='/static/images/brand-logo.png' alt='羽轩 Logo'><div class='brand'>羽轩 · APP INVENTOR</div><h1>开始你的创作</h1><p>输入用户名，即可进入本机工作区。</p>");
    if(!error.isEmpty())out.print("<p class='error' role='alert'>"+escape(error)+"</p>");
    out.print("<form method='post' action='/login'><input type='hidden' name='csrf' value='"+csrf+"'><label for='username'>用户名</label><input id='username' name='username' required maxlength='32' pattern='[A-Za-z0-9]{1,32}' autocomplete='off' spellcheck='false' title='仅允许 1–32 位英文字母和数字' placeholder='例如 Yuxuan2026'><button type='submit'>进入工作区</button></form><p class='hint'>仅允许 1–32 位英文字母和数字，无需密码。此电脑上的项目使用同一个本地工作区。</p></main></html>");
  }
  @Override protected void doPost(HttpServletRequest req,HttpServletResponse resp) throws IOException {
    if(!local(req)){resp.sendError(403);return;}
    if(req.getRequestURI().endsWith("/_shutdown")){
      if(!eq(System.getProperty("offline.control.token"),req.getHeader("X-Offline-Control"))){resp.sendError(403);return;}
      final Object delegate=ApiProxy.getDelegate();
      resp.setContentType("text/plain");resp.getWriter().print("stopping");resp.flushBuffer();
      new Thread(() -> {try{Thread.sleep(250);delegate.getClass().getMethod("stop").invoke(delegate);}catch(Exception e){e.printStackTrace();}finally{System.exit(0);}},"offline-shutdown").start();return;
    }
    req.setCharacterEncoding("UTF-8");
    HttpSession session=req.getSession(false);
    if(session==null || !eq((String)session.getAttribute("offline.csrf"),req.getParameter("csrf"))){resp.sendError(403,"请刷新入口页面后重试");return;}
    String username=req.getParameter("username");
    if(username==null || !username.matches("[A-Za-z0-9]{1,32}")){resp.setStatus(400);render(req,resp,"用户名只能包含 1–32 位英文字母和数字，不能包含空格、中文或符号。");return;}
    try {
      User user;
      synchronized(ACCOUNT_LOCK){
        Properties p=account();
        // A single local workspace survives the change from password login to a display name.
        // Preserve its datastore identity even when the entered display name changes.
        String email=p.getProperty("email");
        if(email==null || email.isEmpty())email=username.toLowerCase(Locale.ROOT)+"@offline.local";
        user=storage.getUserFromEmail(email);
        ensureClassicLayout(user.getUserId());
        p.setProperty("username",username); p.setProperty("email",email);
        Files.createDirectories(accountPath().getParent());
        Path temp=accountPath().resolveSibling("account.properties.tmp");
        try(OutputStream stream=Files.newOutputStream(temp)){p.store(stream,"Local workspace display name and persistent datastore identity. No password required.");}
        Files.move(temp,accountPath(),StandardCopyOption.REPLACE_EXISTING);
      }
      session.invalidate(); req.getSession(true);
      OdeAuthFilter.UserInfo info=new OdeAuthFilter.UserInfo();info.setUserId(user.getUserId());info.setIsAdmin(false);
      resp.addHeader("Set-Cookie","OfflineDisplayName="+username+"; Path=/; SameSite=Lax");
      resp.addHeader("Set-Cookie","AppInventor="+info.buildCookie(false)+"; Path=/; HttpOnly; SameSite=Lax");
      resp.setHeader("Cache-Control","no-store");resp.sendRedirect("/?locale=zh_CN");
    }catch(Exception e){getServletContext().log("Local account operation failed",e);resp.setStatus(500);render(req,resp,"本地工作区打开失败，请查看启动器中的日志。");}
  }
}
