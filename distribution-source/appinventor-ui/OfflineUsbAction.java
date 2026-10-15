package com.google.appinventor.client.actions;

import com.google.appinventor.client.Ode;
import com.google.appinventor.client.explorer.commands.*;
import com.google.appinventor.shared.rpc.project.ProjectNode;
import com.google.appinventor.shared.rpc.project.ProjectRootNode;
import com.google.appinventor.shared.rpc.project.youngandroid.YoungAndroidProjectNode;
import com.google.gwt.core.client.GWT;
import com.google.gwt.user.client.Command;

/** Desktop USB deployment uses the same save/YAIL/build chain as local APK export. */
public final class OfflineUsbAction {
  private static boolean building;
  private static int generation;

  public static native void register() /*-{
    $wnd.OfflineAppInventor = {
      buildForUsb: $entry(function(ticket) {
        return @com.google.appinventor.client.actions.OfflineUsbAction::build(Ljava/lang/String;)(ticket);
      })
    };
    $wnd.dispatchEvent(new $wnd.Event('offline-appinventor-ready'));
  }-*/;

  private static native void notifyReady(String ticket, String path) /*-{
    if ($wnd.offlineUsbBuildReady) $wnd.offlineUsbBuildReady(ticket, path);
  }-*/;

  private static native void notifyFailure(String ticket, String message) /*-{
    if ($wnd.offlineUsbBuildFailed) $wnd.offlineUsbBuildFailed(ticket, message);
  }-*/;

  private static boolean build(final String ticket) {
    final Ode ode = Ode.getInstance();
    ProjectRootNode root = ode.getCurrentYoungAndroidProjectRootNode();
    if (root == null || ode.isReadOnly() || building) return false;
    building = true;
    final int current = ++generation;
    final boolean[] completed = {false};
    final ChainableCommand deliver = new ChainableCommand() {
      @Override public boolean willCallExecuteNextCommand() { return false; }
      @Override public void execute(ProjectNode node) {
        if (completed[0] || current != generation) return;
        completed[0] = true;
        building = false;
        notifyReady(ticket, GWT.getModuleBaseURL() + "download/project-output/"
            + node.getProjectId() + "/" + YoungAndroidProjectNode.YOUNG_ANDROID_TARGET_ANDROID);
      }
    };
    String target = YoungAndroidProjectNode.YOUNG_ANDROID_TARGET_ANDROID;
    ChainableCommand chain = new SaveAllEditorsCommand(new GenerateYailCommand(
        new BuildCommand(target, false, false, false, false,
            new WaitForBuildResultCommand(target, deliver), deliver)));
    try {
      chain.startExecuteChain("OfflineUsbAction", root, new Command() {
        @Override public void execute() {
          if (completed[0] || current != generation) return;
          completed[0] = true;
          building = false;
          notifyFailure(ticket, "APK 构建失败或已取消，请查看 App Inventor 的构建错误。");
        }
      });
    } catch (RuntimeException e) {
      if (!completed[0] && current == generation) {
        completed[0] = true;
        building = false;
        notifyFailure(ticket, "无法开始构建，请检查当前项目后重试。");
      }
    }
    return true;
  }
}
