import java.nio.file.*;
import jdk.internal.org.objectweb.asm.*;

public final class PatchBlobStorage {
  public static void main(String[] args) throws Exception {
    byte[] source = Files.readAllBytes(Paths.get(args[0]));
    ClassWriter writer = new ClassWriter(ClassWriter.COMPUTE_MAXS);
    ClassVisitor visitor = new ClassVisitor(Opcodes.ASM7, writer) {
      @Override public MethodVisitor visitMethod(int access, String name, String desc, String signature, String[] exceptions) {
        if (name.equals("getFileForBlob") && desc.equals("(Lcom/google/appengine/api/blobstore/BlobKey;)Ljava/io/File;")) {
          MethodVisitor mv = super.visitMethod(access, name, desc, signature, exceptions);
          mv.visitCode();
          mv.visitVarInsn(Opcodes.ALOAD, 0);
          mv.visitFieldInsn(Opcodes.GETFIELD, "com/google/appengine/api/blobstore/dev/FileBlobStorage", "rootDirectory", "Ljava/io/File;");
          mv.visitVarInsn(Opcodes.ALOAD, 1);
          mv.visitMethodInsn(Opcodes.INVOKESTATIC, "com/google/appengine/api/blobstore/dev/BlobFileNames", "resolve", "(Ljava/io/File;Lcom/google/appengine/api/blobstore/BlobKey;)Ljava/io/File;", false);
          mv.visitInsn(Opcodes.ARETURN);
          mv.visitMaxs(2, 2);
          mv.visitEnd();
          return null;
        }
        MethodVisitor original = super.visitMethod(access, name, desc, signature, exceptions);
        return new MethodVisitor(Opcodes.ASM7, original) {
          @Override public void visitMethodInsn(int opcode, String owner, String method, String descriptor, boolean itf) {
            if (owner.equals("java/io/File") && method.equals("delete") && descriptor.equals("()Z")) {
              super.visitVarInsn(Opcodes.ALOAD, 0);
              super.visitFieldInsn(Opcodes.GETFIELD, "com/google/appengine/api/blobstore/dev/FileBlobStorage$4", "val$blobKey", "Lcom/google/appengine/api/blobstore/BlobKey;");
              super.visitMethodInsn(Opcodes.INVOKESTATIC, "com/google/appengine/api/blobstore/dev/BlobFileNames", "delete", "(Ljava/io/File;Lcom/google/appengine/api/blobstore/BlobKey;)Z", false);
            } else super.visitMethodInsn(opcode, owner, method, descriptor, itf);
          }
        };
      }
    };
    new ClassReader(source).accept(visitor, 0);
    Files.write(Paths.get(args[1]), writer.toByteArray());
  }
}
