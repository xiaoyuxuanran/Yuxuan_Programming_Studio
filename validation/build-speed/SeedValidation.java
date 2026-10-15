import com.google.appinventor.buildserver.Project;
import com.google.appinventor.buildserver.context.AndroidCompilerContext;
import com.google.appinventor.buildserver.context.AndroidPaths;
import com.google.appinventor.buildserver.context.CompilerContext;
import com.google.appinventor.buildserver.context.Resources;
import com.google.appinventor.buildserver.tasks.android.RunD8;
import com.google.appinventor.buildserver.util.Execution;
import java.io.File;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Map;

public final class SeedValidation {
  static Method method(String name, Class<?>... types) throws Exception {
    Method m = RunD8.class.getDeclaredMethod(name, types); m.setAccessible(true); return m;
  }
  static void resetResources() throws Exception {
    Field f = Resources.class.getDeclaredField("RESOURCES"); f.setAccessible(true); ((Map<?,?>) f.get(null)).clear();
    f = Resources.class.getDeclaredField("seedManifest"); f.setAccessible(true); f.set(null, null);
  }
  static void ensure(boolean result, String label) {
    if (!result) throw new AssertionError(label);
    System.out.println("PASS " + label);
  }
  static AndroidCompilerContext context(File base, int min) throws Exception {
    File project = new File(base, "project-" + min + ".properties");
    Files.write(project.toPath(), ("androidminsdk=" + min + "\nmain=appinventor.ai_test.Test.Screen1\nname=Test\nsource=../src\nassets=../assets\nbuild=../build\n").getBytes(StandardCharsets.UTF_8));
    return new CompilerContext.Builder<AndroidPaths, AndroidCompilerContext>(new Project(project), "apk")
        .withClass(AndroidCompilerContext.class).withTypes(new java.util.HashSet<>())
        .withBlocks(new java.util.HashMap<>()).withBlockPermissions(new java.util.HashSet<>())
        .withFormOrientations(new java.util.HashMap<>())
        .withReporter(new com.google.appinventor.buildserver.Reporter(null))
        .withKeystore(new File(base, "unused-test-keystore").toString()).withOutput("fixture").build();
  }
  public static void main(String[] args) throws Exception {
    File base = new File(args[0]); base.mkdirs();
    Method hashFile = method("sha256", File.class);
    Method hashText = method("sha256", String.class);
    File hashTarget = new File(base, "same-path.dat");
    Files.write(hashTarget.toPath(), new byte[]{1,2,3}); long time = hashTarget.lastModified();
    String first = (String) hashFile.invoke(null, hashTarget);
    Files.write(hashTarget.toPath(), new byte[]{1,2,4}); hashTarget.setLastModified(time);
    ensure(!first.equals(hashFile.invoke(null, hashTarget)), "same path/size/mtime changed contents invalidates hash");
    Method fingerprint = method("environmentFingerprint", AndroidCompilerContext.class);
    String fp14 = (String) fingerprint.invoke(null, context(base, 14));
    String fp19 = (String) fingerprint.invoke(null, context(base, 19));
    ensure(!fp14.equals(fp19), "min API changes cache fingerprint");
    Resources resources = new Resources();
    String d8 = (String) hashFile.invoke(null, new File(resources.getD8Jar()));
    String android = (String) hashFile.invoke(null, new File(resources.getAndroidRuntime()));
    ensure(fp14.equals(hashText.invoke(null, "yuxuan-d8-intermediate-v2\n" + d8 + "\n" + android + "\n14\n")), "fingerprint includes exact D8/Android contents");
    String changedD8 = (String) hashText.invoke(null, "yuxuan-d8-intermediate-v2\n" + first + "\n" + android + "\n14\n");
    ensure(!fp14.equals(changedD8), "tool content changes cache fingerprint");
    Method validDex = method("validDex", File.class);
    File dex = new File(args[1]);
    ensure((Boolean) validDex.invoke(null, dex), "real bundled DEX checksum accepted");
    File damaged = new File(base, "damaged.dex"); byte[] bytes = Files.readAllBytes(dex.toPath()); bytes[100] ^= 1;
    Files.write(damaged.toPath(), bytes);
    ensure(!(Boolean) validDex.invoke(null, damaged), "corrupted DEX checksum rejected");
    String goodResource = resources.getResource("/files/annotation.jar");
    String expected = (String) hashFile.invoke(null, new File(goodResource));
    System.setProperty("appinventor.resourceSeedDir", args[2]); resetResources();
    String fallback = new Resources().getResource("/files/annotation.jar");
    ensure(!new File(fallback).toPath().startsWith(new File(args[2]).toPath())
        && expected.equals(hashFile.invoke(null, new File(fallback))), "corrupted resource falls back to original JAR");
    File pidFile = new File(base, "child.pid"); File endFile = new File(base, "child.end");
    Files.deleteIfExists(pidFile.toPath()); Files.deleteIfExists(endFile.toPath());
    File sleeper = new File(base, "sleep.py");
    Files.write(sleeper.toPath(), ("import os,pathlib,time\npathlib.Path(r'" + pidFile + "').write_text(str(os.getpid()))\ntime.sleep(8)\npathlib.Path(r'" + endFile + "').write_text('orphan')\n").getBytes(StandardCharsets.UTF_8));
    final boolean[] status = new boolean[]{true};
    Thread worker = new Thread(() -> status[0] = Execution.execute(base, new String[]{args[3], sleeper.toString()}, System.out, System.err, 30));
    worker.start(); for (int i=0;i<50 && !pidFile.isFile();i++) Thread.sleep(100);
    ensure(pidFile.isFile(), "cancellable compiler child started"); worker.interrupt(); worker.join(5000);
    ensure(!worker.isAlive() && !status[0], "interrupted build returns failure promptly");
    long pid = Long.parseLong(new String(Files.readAllBytes(pidFile.toPath()), StandardCharsets.UTF_8));
    Thread.sleep(250);
    ensure(!ProcessHandle.of(pid).map(ProcessHandle::isAlive).orElse(false) && !endFile.exists(), "cancelled compiler child terminated without orphan");
  }
}
