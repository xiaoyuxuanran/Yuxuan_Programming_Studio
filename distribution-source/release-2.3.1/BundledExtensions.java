package com.google.appinventor.server;

import com.google.appinventor.server.storage.StorageIo;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;
import org.json.JSONArray;
import org.json.JSONObject;

/** Project-local extension dependencies; exports remain portable to other AI2 servers. */
public final class BundledExtensions {
  private static final Map<String,Map<String,byte[]>> BUNDLES=load();
  private static Map<String,Map<String,byte[]>> load() {
    Map<String,Map<String,byte[]>> result=new LinkedHashMap<>();
    for(String name:new String[]{"MqttTCP","BluetoothLE","ClientSocketAI2Ext"}) {
      Map<String,byte[]> files=new LinkedHashMap<>();
      try(InputStream input=BundledExtensions.class.getResourceAsStream("/bundled-extensions/"+name+".aix")) {
        if(input==null)throw new IOException("Missing bundled extension: "+name);
        try(ZipInputStream zip=new ZipInputStream(input)) {
          ZipEntry entry;byte[] buffer=new byte[8192];
          while((entry=zip.getNextEntry())!=null) {
            if(entry.isDirectory())continue;
            String path=entry.getName();if(path.startsWith("/")||path.contains("..")||path.contains("\\"))throw new IOException("Invalid bundled path");
            ByteArrayOutputStream output=new ByteArrayOutputStream();int n;
            while((n=zip.read(buffer))>0)output.write(buffer,0,n);
            files.put("assets/external_comps/"+path,output.toByteArray());
          }
        }
      }catch(IOException ex){throw new IllegalStateException(ex);}
      result.put(name,files);
    }
    return result;
  }
  public static synchronized void ensure(StorageIo storage,String user,long project) {
    List<String> existing=storage.getProjectSourceFiles(user,project);
    Set<String> types=new HashSet<>(), names=new HashSet<>();
    for(String path:existing) {
      if(!path.startsWith("assets/external_comps/")||!path.endsWith("/components.json"))continue;
      try {
        JSONArray descriptors=new JSONArray(new String(storage.downloadRawFile(user,project,path),StandardCharsets.UTF_8));
        for(int i=0;i<descriptors.length();i++){JSONObject c=descriptors.getJSONObject(i);types.add(c.getString("type"));names.add(c.getString("name"));}
      }catch(RuntimeException ignored){/* Preserve an imported extension that this server cannot parse. */}
    }
    for(Map.Entry<String,Map<String,byte[]>> bundle:BUNDLES.entrySet()) {
      Map<String,byte[]> files=bundle.getValue();
      String descriptor=files.keySet().stream().filter(p->p.endsWith("/components.json")).findFirst().get();
      JSONObject component=new JSONArray(new String(files.get(descriptor),StandardCharsets.UTF_8)).getJSONObject(0);
      if(types.contains(component.getString("type"))||names.contains(component.getString("name"))||existing.contains(descriptor))continue;
      storage.addSourceFilesToProject(user,project,false,files.keySet().toArray(new String[0]));
      for(Map.Entry<String,byte[]> file:files.entrySet())storage.uploadRawFileForce(project,file.getKey(),user,file.getValue());
    }
  }
}
