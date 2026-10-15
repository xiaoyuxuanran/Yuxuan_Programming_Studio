# App Inventor APK cold-build changes (2.2.0)

`RunD8.java` loads release-time library DEX seeds and keeps a private content-addressed fallback cache. Its key includes SHA256 of the input JAR, the exact D8 tool and Android library, and the effective minimum SDK. All DEX hits pass header/file-size/SHA1/Adler32 checks. Writes use a scratch directory followed by atomic publication; user application classes are always recompiled. Legacy input-only MD5 caches are ignored.

`Resources.java` can read pre-expanded fixed resources. A manifest records each resource's SHA256, checked the first time that resource is used in a process. Missing/corrupt seeds fall back to the embedded BuildServer JAR. On Windows, a Unicode install path also uses the original temp extraction to preserve old AAPT compatibility. The Core supplies an ASCII DOS alias for the data directory when needed for Unicode or long paths.

`ProjectBuilder.java` keeps cold/extension builds bounded by 15 minutes instead of 5. A timeout cancels the compiler. Its executor closes after every build. `Execution.java` terminates a child compiler when interrupted. The existing 120-second keytool limit and private-Java/quoted D8 argument-file fixes remain.

Build from the fixed upstream checkout without modifying it:

```powershell
python patch-native-build.py --compile --source-root "PATH_TO_UPSTREAM/appinventor/buildserver/src/com/google/appinventor/buildserver" --native-root "PATH_TO_NATIVE"
python build-speed/prepare-resource-seed.py --native-root "PATH_TO_NATIVE"
python build-speed/prepare-dex-seed.py --native-root "PATH_TO_NATIVE"
python build-speed/validate-seeds.py --native-root "PATH_TO_NATIVE"
```

`prepare-overlays.py` supports Windows or WSL overlay compilation. The seed-generation and real APK validation scripts run on Windows using the bundled JDK11/Python. The source ZIP contains generation scripts and provenance manifests; the installer's `buildserver/dex-seed` and `resource-seed` contain the actual immutable compiled resources. Seeds only cover built-in JARs at min-api 14 and 19; extensions or other minimum SDK values fall back to their own verified private cache.

`benchmark.py` runs a genuine APK build for a tiny, isolated source fixture, records per-task timings, and kills only its own test process tree when done. It creates a temporary per-session DOS alias for legacy Android tools; no user workspace, activation data or signing key is used. Both APK DEX contents and complete output ZIPs remain in local test folders and are not source-release inputs.
