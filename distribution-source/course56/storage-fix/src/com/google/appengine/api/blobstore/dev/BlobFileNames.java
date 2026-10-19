package com.google.appengine.api.blobstore.dev;

import com.google.appengine.api.blobstore.BlobKey;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/** Safe ordinary filenames for Windows; migrate a legacy named stream on first access. */
final class BlobFileNames {
  private BlobFileNames() {}

  // Called from the SDK's original privileged delete action, before metadata removal.
  static synchronized boolean delete(File safe, BlobKey key) {
    File old = new File(safe.getParentFile(), key.getKeyString());
    // Delete the legacy copy first. If that fails, keep the safe copy and report failure.
    if (old.exists() && !old.delete()) return false;
    return safe.delete();
  }

  static synchronized File resolve(File root, BlobKey key) {
    String name = key.getKeyString();
    // Preserve the SDK's traversal rejection, including both platform separators.
    if (name.indexOf('/') >= 0 || name.indexOf('\\') >= 0 || name.equals(".") || name.equals("..")) {
      throw new IllegalArgumentException("illegal blobKey");
    }
    try {
      byte[] digest = MessageDigest.getInstance("SHA-256").digest(name.getBytes(StandardCharsets.UTF_8));
      StringBuilder hex = new StringBuilder("yuxuan_blob_");
      for (byte value : digest) hex.append(String.format("%02x", value & 255));
      File safe = new File(root, hex + ".bin");
      if (safe.exists()) return safe;
      File old = new File(root, name);
      // Do not delete the legacy blob/ADS: older installed versions can still read it.
      // The SDK fetch/store methods invoke us inside their privileged action.
      if (old.isFile()) {
        Path temporary = Files.createTempFile(root.toPath(), "blob-migrate-", ".tmp");
        try {
          // NIO rejects ':' in legacy Windows streams; java.io can read them.
          try (InputStream input = new FileInputStream(old);
               OutputStream output = Files.newOutputStream(temporary)) {
            input.transferTo(output);
          }
          try {
            Files.move(temporary, safe.toPath(), StandardCopyOption.ATOMIC_MOVE);
          } catch (AtomicMoveNotSupportedException ex) {
            Files.move(temporary, safe.toPath(), StandardCopyOption.REPLACE_EXISTING);
          }
        } finally {
          Files.deleteIfExists(temporary);
        }
      }
      return safe;
    } catch (IOException | NoSuchAlgorithmException ex) {
      throw new IllegalStateException("Cannot resolve local blob storage", ex);
    }
  }
}
