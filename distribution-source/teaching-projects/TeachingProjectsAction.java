package com.google.appinventor.client.actions;

import com.google.appinventor.client.Ode;
import com.google.appinventor.client.boxes.ProjectListBox;
import com.google.appinventor.client.explorer.project.Project;
import com.google.appinventor.client.youngandroid.TextValidators;
import com.google.appinventor.shared.rpc.UploadResponse;
import com.google.appinventor.shared.rpc.project.UserProject;

/** Connect the bundled curriculum browser to the normal project import/editor lifecycle. */
public final class TeachingProjectsAction {
  private TeachingProjectsAction() {}

  public static native void register() /*-{
    $wnd.YuxuanTeaching = {
      openExisting: $entry(function(name) {
        return @com.google.appinventor.client.actions.TeachingProjectsAction::openExisting(Ljava/lang/String;)(name);
      }),
      openImported: $entry(function(response) {
        return @com.google.appinventor.client.actions.TeachingProjectsAction::openImported(Ljava/lang/String;)(response);
      }),
      setTeachingView: $entry(function(active) {
        @com.google.appinventor.client.actions.TeachingProjectsAction::setTeachingView(Z)(!!active);
      }),
      validFolderName: $entry(function(name) {
        return @com.google.appinventor.client.youngandroid.TextValidators::isValidFolderName(Ljava/lang/String;)(name);
      })
    };
    $wnd.dispatchEvent(new $wnd.Event('yuxuan-teaching-ready'));
  }-*/;

  private static String openExisting(String name) {
    Project project = Ode.getInstance().getProjectManager().getProject(name);
    if (project == null) return "missing";
    if (project.isInTrash()) return "trash";
    Ode.getInstance().openYoungAndroidProjectInDesigner(project);
    return "opened";
  }

  private static String openImported(String response) {
    UploadResponse upload = UploadResponse.extractUploadResponse(response);
    if (upload == null || upload.getStatus() != UploadResponse.Status.SUCCESS) return "error";
    UserProject info = UserProject.valueOf(upload.getInfo());
    Project project = Ode.getInstance().getProjectManager().getProject(info.getProjectId());
    if (project == null) project = Ode.getInstance().getProjectManager().addProject(info);
    Ode.getInstance().openYoungAndroidProjectInDesigner(project);
    return "opened";
  }

  private static void setTeachingView(boolean active) {
    Ode ode = Ode.getInstance();
    ode.getProjectToolbar().setVisible(!active);
    // Clear selection from the hidden personal list before any toolbar action can run.
    if (ProjectListBox.getProjectListBox() != null
        && ode.getFolderManager().getGlobalFolder() != null) {
      ProjectListBox box = ProjectListBox.getProjectListBox();
      box.getProjectList().refresh(false);
      if ("projects".equals(box.getElement().getAttribute("data-yuxuan-project-box"))) {
        box.setCaption(active ? "教学项目" : Ode.MESSAGES.projectListBoxCaption());
      }
    }
  }
}
