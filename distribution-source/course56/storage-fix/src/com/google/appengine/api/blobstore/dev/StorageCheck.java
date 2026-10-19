package com.google.appengine.api.blobstore.dev;
import com.google.appengine.api.blobstore.BlobKey;
import java.io.*;
import java.nio.file.*;
import java.util.Arrays;
public final class StorageCheck {
  public static void main(String[] args) throws Exception {
    File root = new File(args[0]); root.mkdirs();
    FileBlobStorage store = new FileBlobStorage(root, null);
    byte[] expected = "中文课程资源".getBytes("UTF-8");
    for (int i=0; i<1400; i++) {
      BlobKey key = new BlobKey("encoded_gs_key:course-test-" + i);
      try(OutputStream out = store.storeBlob(key)) {out.write(expected);}
      if(!store.hasBlob(key)) throw new AssertionError("missing " + i);
      try(InputStream in = store.fetchBlob(key)) {
        if(!Arrays.equals(expected,in.readAllBytes()))throw new AssertionError("bytes " + i);
      }
      if(store.getFileForBlob(key).getName().contains(":"))throw new AssertionError("unsafe filename");
    }
    BlobKey legacy = new BlobKey("encoded_gs_key:legacy-migration");
    try(OutputStream out = new FileOutputStream(new File(root,legacy.getKeyString()))) {out.write(expected);}
    try(InputStream in = store.fetchBlob(legacy)) {
      if(!Arrays.equals(expected,in.readAllBytes()))throw new AssertionError("legacy migration");
    }
    if(!new File(root,legacy.getKeyString()).exists())throw new AssertionError("legacy removed");
    // Exercise the patched privileged SDK action; metadata validation stays in deleteBlob.
    var ctor=Class.forName("com.google.appengine.api.blobstore.dev.FileBlobStorage$4")
        .getDeclaredConstructor(FileBlobStorage.class, BlobKey.class);
    ctor.setAccessible(true);
    var action=(java.security.PrivilegedExceptionAction<?>)ctor.newInstance(store,legacy);
    java.security.AccessController.doPrivileged(action);
    if(store.hasBlob(legacy))throw new AssertionError("deleted legacy blob resurrected");
    if(new File(root,legacy.getKeyString()).exists())throw new AssertionError("legacy copy remains");
    byte[] replacement="new content".getBytes("UTF-8");
    try(OutputStream out=store.storeBlob(legacy)){out.write(replacement);}
    try(InputStream in=store.fetchBlob(legacy)){
      if(!Arrays.equals(replacement,in.readAllBytes()))throw new AssertionError("overwrite after delete");
    }
    BlobKey longKey=new BlobKey("encoded_gs_key:"+"x".repeat(2000));
    try(OutputStream out=store.storeBlob(longKey)){out.write(expected);}
    if(!store.hasBlob(longKey))throw new AssertionError("long key");
    for(String bad:new String[]{"../escape","..\\escape","/absolute","C:\\absolute"}) {
      try {store.getFileForBlob(new BlobKey(bad));throw new AssertionError("accepted traversal");}
      catch(IllegalArgumentException expectedError) {}
    }
    System.out.println("PASS: 1400 blobs, byte equality, legacy ADS migration, privileged deletion without resurrection, overwrite, long key, traversal rejection");
  }
}
