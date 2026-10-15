"""Make reproducible overlays from fixed upstream; compile with the bundled JDK11."""
import argparse, difflib, os, pathlib, subprocess

HERE = pathlib.Path(__file__).resolve().parent
WORK = HERE.parent
UPSTREAM = pathlib.Path(r'\\wsl.localhost\Ubuntu-24.04\home\yuxuan\appinventor-dev\appinventor-sources\appinventor\buildserver\src\com\google\appinventor\buildserver') if os.name == 'nt' else pathlib.Path('/home/yuxuan/appinventor-dev/appinventor-sources/appinventor/buildserver/src/com/google/appinventor/buildserver')
OUT = WORK / 'native-patches'

def save(relative, after, name=None):
    before = (UPSTREAM / relative).read_text(encoding='utf-8')
    target = OUT / (name or pathlib.Path(relative).name)
    target.write_text(after, encoding='utf-8')
    (OUT / (target.stem + '-offline.patch')).write_text(''.join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True), fromfile=relative, tofile=relative)), encoding='utf-8')
    return target

def project_builder():
    code = (UPSTREAM / 'ProjectBuilder.java').read_text(encoding='utf-8')
    code = code.replace('private static final int MAX_BUILD_TIMEOUT_SECONDS = 60 * 5; // 5 minutes',
                        'private static final int MAX_BUILD_TIMEOUT_SECONDS = 60 * 15; // Bounded cold/extension build budget')
    code = code.replace('import java.util.concurrent.Executors;', 'import java.util.concurrent.Executors;\nimport java.util.concurrent.ExecutorService;')
    code = code.replace('Future<Boolean> executor = Executors.newSingleThreadExecutor().submit(compiler);',
                        'ExecutorService buildExecutor = Executors.newSingleThreadExecutor();\n'
                        '        Future<Boolean> executor = buildExecutor.submit(compiler);')
    code = code.replace('LOG.severe("Build has timed out");', 'executor.cancel(true);\n          LOG.severe("Build has timed out");')
    code = code.replace('context.getReporter().error("Build has timed out");\n          success = false;\n        }',
                        'context.getReporter().error("Build has timed out (15 minute limit)");\n'
                        '          success = false;\n        } finally {\n          buildExecutor.shutdownNow();\n        }')
    code = code.replace('Execution.Timeout.SHORT)) {\n      if (keyStoreFile.length() > 0)',
                        'Execution.Timeout.LONG)) {\n      if (keyStoreFile.length() > 0)')
    return save('ProjectBuilder.java', code)

def execution():
    code = (UPSTREAM / 'util/Execution.java').read_text(encoding='utf-8')
    code = code.replace('    try {\n      Process process = Runtime.getRuntime().exec(command, null, workingDir);',
                        '    Process process = null;\n    try {\n'
                        '      if (Thread.currentThread().isInterrupted()) {\n        return false;\n      }\n'
                        '      process = Runtime.getRuntime().exec(command, null, workingDir);')
    code = code.replace('      return process.exitValue() == 0;\n    } catch (Exception e) {',
                        '      return process.exitValue() == 0;\n    } catch (InterruptedException e) {\n'
                        '      if (process != null) {\n        process.destroyForcibly();\n      }\n'
                        '      Thread.currentThread().interrupt();\n'
                        '      err.println("Process stopped because the build was cancelled");\n'
                        '      return false;\n    } catch (Exception e) {')
    return save('util/Execution.java', code)

def resources():
    code = (UPSTREAM / 'context/Resources.java').read_text(encoding='utf-8')
    code = code.replace('import java.io.IOException;', '''import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Properties;''')
    code = code.replace('          String basename = PathUtil.basename(resourcePath);', '''          file = bundledResource(resourcePath);
          if (file != null) {
            RESOURCES.put(resourcePath, file);
            return file.getAbsolutePath();
          }
          String basename = PathUtil.basename(resourcePath);''')
    pos = code.index('  public List<File> getDexFiles()')
    code = code[:pos] + '''  private static Properties seedManifest;

  private static File bundledResource(String resourcePath) {
    String folder = System.getProperty("appinventor.resourceSeedDir");
    if (folder == null || !(resourcePath.startsWith("/files/") || resourcePath.startsWith("/tools/"))) {
      return null;
    }
    try {
      Path base = new File(folder).toPath().toAbsolutePath().normalize();
      Path path = base.resolve(resourcePath.substring(1)).normalize();
      if (!path.startsWith(base)) {
        return null;
      }
      // Old Windows AAPT cannot read ZIP resources on a Unicode path. Its existing
      // temp extraction receives the Core's ASCII DOS-drive alias and stays reliable.
      if (System.getProperty("os.name").startsWith("Windows")) {
        if (path.toString().length() >= 200) {
          return null;
        }
        for (char c : path.toString().toCharArray()) {
          if (c > 127) {
            return null;
          }
        }
      }
      if (seedManifest == null) {
        seedManifest = new Properties();
        try (InputStream in = java.nio.file.Files.newInputStream(base.resolve("manifest.properties"))) {
          seedManifest.load(in);
        }
      }
      String expected = seedManifest.getProperty(resourcePath.substring(1));
      if (expected == null || !java.nio.file.Files.isRegularFile(path)) {
        return null;
      }
      MessageDigest digest = MessageDigest.getInstance("SHA-256");
      try (InputStream in = java.nio.file.Files.newInputStream(path)) {
        byte[] buffer = new byte[65536];
        int count;
        while ((count = in.read(buffer)) != -1) {
          digest.update(buffer, 0, count);
        }
      }
      StringBuilder actual = new StringBuilder();
      for (byte b : digest.digest()) {
        actual.append(String.format("%02x", b & 255));
      }
      return expected.equals(actual.toString()) ? path.toFile() : null;
    } catch (IOException | NoSuchAlgorithmException | IllegalArgumentException e) {
      return null;  // Missing/corrupt seed always falls back to the original JAR resource.
    }
  }

''' + code[pos:]
    return save('context/Resources.java', code)

def d8():
    code = (UPSTREAM / 'tasks/android/RunD8.java').read_text(encoding='utf-8')
    code = code.replace('import java.io.IOException;', '''import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.StandardCopyOption;
import java.nio.file.AtomicMoveNotSupportedException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.zip.Adler32;''')
    code = code.replace('    try {\n      recordForMainDex', '    try {\n      final String environment = environmentFingerprint(context);\n      recordIfNeeded')
    code = code.replace('preDexLibrary(context,', 'preDexLibrary(context, environment,')
    code = code.replace('recordForMainDex(', 'recordIfNeeded(')
    code = code.replace('arguments.add("java");', 'arguments.add(new File(System.getProperty("java.home"), "bin/java").getAbsolutePath());')
    code = code.replace('ps.println(arg);', r'ps.println("\"" + arg.replace("\\", "\\\\").replace("\"", "\\\"") + "\"");')
    start = code.index('  private static File preDexLibrary(')
    code = code[:start] + '''  private static File recordIfNeeded(File input, Set<String> mainDexClasses) throws IOException {
    // The Proguard-rule branch never uses the discovered class-name list.
    return USE_D8_PROGUARD_RULES ? input : recordForMainDex(input, mainDexClasses);
  }

  private static String sha256(File file) throws IOException {
    try {
      MessageDigest digest = MessageDigest.getInstance("SHA-256");
      try (InputStream in = Files.newInputStream(file.toPath())) {
        byte[] buffer = new byte[65536];
        int count;
        while ((count = in.read(buffer)) != -1) {
          digest.update(buffer, 0, count);
        }
      }
      return hex(digest.digest());
    } catch (NoSuchAlgorithmException e) {
      throw new IOException(e);
    }
  }

  private static String sha256(String value) throws IOException {
    try {
      return hex(MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8)));
    } catch (NoSuchAlgorithmException e) {
      throw new IOException(e);
    }
  }

  private static String hex(byte[] value) {
    StringBuilder result = new StringBuilder(value.length * 2);
    for (byte b : value) {
      result.append(String.format("%02x", b & 0xff));
    }
    return result.toString();
  }

  private static String environmentFingerprint(AndroidCompilerContext context) throws IOException {
    // A library's dex depends on its contents, the exact D8/Android libraries and min-api.
    // Do not accept the legacy cache, which keyed only on the input JAR.
    return sha256("yuxuan-d8-intermediate-v2\\n"
        + sha256(new File(context.getResources().getD8Jar())) + "\\n"
        + sha256(new File(context.getResources().getAndroidRuntime())) + "\\n"
        + AndroidBuildUtils.computeMinSdk(context) + "\\n");
  }

  private static boolean validDex(File file) {
    try {
      byte[] bytes = Files.readAllBytes(file.toPath());
      if (bytes.length < 112 || bytes[0] != 'd' || bytes[1] != 'e' || bytes[2] != 'x'
          || bytes[3] != '\\n' || bytes[7] != 0) {
        return false;
      }
      long declaredSize = ((long) bytes[32] & 255) | (((long) bytes[33] & 255) << 8)
          | (((long) bytes[34] & 255) << 16) | (((long) bytes[35] & 255) << 24);
      if (declaredSize != bytes.length) {
        return false;
      }
      MessageDigest digest = MessageDigest.getInstance("SHA-1");
      digest.update(bytes, 32, bytes.length - 32);
      if (!Arrays.equals(Arrays.copyOfRange(bytes, 12, 32), digest.digest())) {
        return false;
      }
      Adler32 checksum = new Adler32();
      checksum.update(bytes, 12, bytes.length - 12);
      long declaredChecksum = ((long) bytes[8] & 255) | (((long) bytes[9] & 255) << 8)
          | (((long) bytes[10] & 255) << 16) | (((long) bytes[11] & 255) << 24);
      return declaredChecksum == checksum.getValue();
    } catch (IOException | NoSuchAlgorithmException e) {
      return false;
    }
  }

  private static File preDexLibrary(AndroidCompilerContext context, String environment, File input)
      throws IOException {
    synchronized (PREDEX_CACHE) {
      File cacheDir = new File(context.getDexCacheDir());
      Files.createDirectories(cacheDir.toPath());
      String filename = "dex-v2-" + sha256(environment + "\\n" + sha256(input)) + ".dex";
      File dexedLib = new File(cacheDir, filename);
      if (validDex(dexedLib)) {
        context.getReporter().info(String.format("Using pre-dexed %1$s <- %2$s", filename, input));
        return dexedLib;
      }
      String seedDir = System.getProperty("appinventor.dexSeedDir");
      if (seedDir != null) {
        File seed = new File(seedDir, filename);
        if (validDex(seed)) {
          context.getReporter().info(String.format("Using bundled pre-dexed %1$s <- %2$s", filename, input));
          return seed;
        }
      }
      // A private scratch directory and atomic publication prevent a killed/interrupted
      // compiler from leaving a partial dex that the next build mistakes for a cache hit.
      Path scratch = Files.createTempDirectory(cacheDir.toPath(), "predex-");
      try {
        boolean success = runD8(context, Collections.singleton(input), null, scratch.toString(), filename);
        File generated = scratch.resolve(filename).toFile();
        if (!success || !validDex(generated)) {
          return input;
        }
        try {
          Files.move(generated.toPath(), dexedLib.toPath(),
              StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (AtomicMoveNotSupportedException e) {
          Files.move(generated.toPath(), dexedLib.toPath(), StandardCopyOption.REPLACE_EXISTING);
        }
        return dexedLib;
      } finally {
        File[] leftovers = scratch.toFile().listFiles();
        if (leftovers != null) {
          for (File file : leftovers) {
            Files.deleteIfExists(file.toPath());
          }
        }
        Files.deleteIfExists(scratch);
      }
    }
  }
}
'''
    return save('tasks/android/RunD8.java', code)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--compile', action='store_true')
    parser.add_argument('--source-root', type=pathlib.Path, default=UPSTREAM)
    parser.add_argument('--output', type=pathlib.Path, default=OUT)
    parser.add_argument('--native-root', type=pathlib.Path, default=WORK / 'native')
    args = parser.parse_args()
    UPSTREAM = args.source_root; OUT = args.output
    OUT.mkdir(parents=True, exist_ok=True)
    sources = [project_builder(), execution(), resources(), d8()]
    if args.compile:
        native = args.native_root
        classes = native / 'buildserver/classes'
        javac = native / 'runtime/java11/bin/javac.exe' if os.name == 'nt' else pathlib.Path('/usr/lib/jvm/java-11-openjdk-amd64/bin/javac')
        subprocess.run([str(javac), '-encoding', 'UTF-8',
                        '-cp', str(classes) + os.pathsep + str(native / 'buildserver/lib/*'), '-d', str(classes)]
                       + [str(p) for p in sources], check=True)
    print('Prepared build-speed overlays: ' + ', '.join(p.name for p in sources))
