<?php
declare(strict_types=1);
require_once __DIR__.'/../linqing/core.php';
const J_STORE=__DIR__.'/storage';
function j_headers():void {
    header('Cache-Control: no-store');header('X-Content-Type-Options: nosniff');header('Referrer-Policy: no-referrer');header('X-Frame-Options: DENY');
}
function j_session():void {
    ini_set('session.use_strict_mode','1');ini_set('session.use_only_cookies','1');session_name('yuxuan_activation_admin');
    session_set_cookie_params(['lifetime'=>0,'path'=>'/jihuo/','secure'=>!empty($_SERVER['HTTPS'])&&$_SERVER['HTTPS']!=='off','httponly'=>true,'samesite'=>'Strict']);session_start();
    if(!isset($_SESSION['csrf']))$_SESSION['csrf']=bin2hex(random_bytes(32));
    if(isset($_SESSION['last'])&&time()-$_SESSION['last']>1800)unset($_SESSION['licenseUser'],$_SESSION['licenseVersion']);
}
function j_account():?array {return with_state(function(&$s){return $s['account']??null;});}
function j_authenticated():bool {
    $a=j_account();return $a&&!empty($_SESSION['licenseUser'])&&hash_equals($a['username'],$_SESSION['licenseUser'])&&($_SESSION['licenseVersion']??0)===$a['version'];
}
function j_auth():void {if(!j_authenticated())fail('请先输入管理员密码',401);$_SESSION['last']=time();}
function j_csrf():void {if(!hash_equals($_SESSION['csrf']??'',$_SERVER['HTTP_X_CSRF_TOKEN']??''))fail('会话验证失败，请刷新页面',403);}
function j_sodium():void {if(!function_exists('sodium_crypto_sign_keypair'))fail('请在宝塔 PHP 中启用 sodium 扩展后使用激活功能',503);}
function j_state(callable $callback) {
    if(!is_dir(J_STORE)&&!mkdir(J_STORE,0700,true))fail('激活数据目录不可写',500);
    $lock=fopen(J_STORE.'/lock.php','c+');if(!$lock||!flock($lock,LOCK_EX))fail('服务繁忙，请重试',503);
    try{
        if(fstat($lock)['size']===0){fwrite($lock,CMS_GUARD);fflush($lock);}@chmod(J_STORE.'/lock.php',0600);
        $s=load_data(J_STORE.'/state.php',['schema'=>1,'codes'=>[],'challenges'=>[],'rates'=>[],'logs'=>[],'secret'=>null,'public'=>null]);
        // Errors are returned and committed so rate limits and used challenges survive failures.
        try{$result=$callback($s);}catch(RuntimeException $e){if($e->getCode()<400||$e->getCode()>599)throw $e;$result=['error'=>$e->getMessage(),'status'=>$e->getCode()];}
        save_data(J_STORE.'/state.php',$s);@chmod(J_STORE.'/state.php',0600);return $result;
    }finally{flock($lock,LOCK_UN);fclose($lock);}
}
function j_log(array &$s,string $action,string $detail=''):void {
    array_unshift($s['logs'],['date'=>date(DATE_ATOM),'action'=>$action,'detail'=>$detail,'user'=>$_SESSION['licenseUser']??'软件客户端']);$s['logs']=array_slice($s['logs'],0,200);
}
function j_rate(array &$s,string $type,int $limit,int $seconds):void {
    foreach($s['rates'] as $k=>$r)if(($r['updated']??0)<time()-3600)unset($s['rates'][$k]);
    $key=hash('sha256',$type.':'.($_SERVER['REMOTE_ADDR']??''));$r=$s['rates'][$key]??['times'=>[]];
    $r['times']=array_values(array_filter($r['times'],function($t)use($seconds){return $t>time()-$seconds;}));
    if(count($r['times'])>=$limit)fail('请求过于频繁，请稍后重试',429);
    if(!isset($s['rates'][$key])&&count($s['rates'])>=2000)fail('服务繁忙，请稍后重试',429);
    $r['times'][]=time();$r['updated']=time();$s['rates'][$key]=$r;
}
function j_keys(array &$s):void {
    j_sodium();if($s['secret']!==null)return;$pair=sodium_crypto_sign_keypair();$s['secret']=base64_encode(sodium_crypto_sign_secretkey($pair));$s['public']=base64_encode(sodium_crypto_sign_publickey($pair));
}
function j_product($v):string {$v=text_field($v,80,true);if(!preg_match('/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$/',$v))fail('软件标识只能包含英文字母、数字、点、下划线和短横线',400);return $v;}
function j_offline_products():array {
    $file=__DIR__.'/offline-products.php';$products=is_file($file)?require $file:[];
    return is_array($products)?array_values(array_filter($products,'is_string')):[];
}
function j_code($v):string {$v=strtoupper(text_field($v,100,true));if(!preg_match('/^YX(?:-[A-F0-9]{8}){4}$/',$v))fail('激活码格式不正确',400);return $v;}
function j_public_code(array $row):array {unset($row['codeHash']);return $row;}
function j_expiry($value):?int {
    $value=text_field($value,10);if($value==='')return null;$dt=DateTime::createFromFormat('!Y-m-d',$value);if(!$dt||$dt->format('Y-m-d')!==$value)fail('有效期日期不正确',400);
    $dt->setTime(23,59,59);if($dt->getTimestamp()<=time())fail('有效期必须晚于当前时间',400);return $dt->getTimestamp();
}
function j_admin_action(array &$s,string $action,array $b):array {
    if($action==='list')return ['codes'=>array_map('j_public_code',array_values($s['codes'])),'logs'=>$s['logs'],'publicKey'=>$s['public'],'sodium'=>function_exists('sodium_crypto_sign_keypair')];
    if($action==='generate'){
        j_keys($s);$product=j_product($b['product']??'');$count=(int)($b['count']??1);if($count<1||$count>50)fail('一次可生成 1–50 个激活码',400);
        if(count($s['codes'])+$count>5000)fail('激活码数量已达 5000 个，请清理后重试',400);
        $expires=j_expiry($b['expires']??'');$note=text_field($b['note']??'',600);$result=[];
        for($i=0;$i<$count;$i++){$code='YX-'.implode('-',str_split(strtoupper(bin2hex(random_bytes(16))),8));$id=bin2hex(random_bytes(16));
            $row=['id'=>$id,'codeHash'=>hash('sha256',$code),'mask'=>'YX-••••-••••-••••-'.substr($code,-8),'product'=>$product,'note'=>$note,'expires'=>$expires,'created'=>date(DATE_ATOM),'enabled'=>true,'binding'=>null,'lastSeen'=>null,'version'=>1];$s['codes'][$id]=$row;$result[]=['id'=>$id,'code'=>$code];
        }j_log($s,'生成激活码',$product.' · '.$count.' 个');return ['codes'=>$result,'publicKey'=>$s['public']];
    }
    $id=text_field($b['id']??'',32,true);if(!isset($s['codes'][$id]))fail('激活码不存在',404);$row=&$s['codes'][$id];
    if((int)($b['version']??-1)!==$row['version'])fail('激活码已更新，请刷新列表后重试',409);
    if($action==='unbind'){$row['binding']=null;$row['lastSeen']=null;}
    elseif($action==='disable')$row['enabled']=false;
    elseif($action==='enable')$row['enabled']=true;
    elseif($action==='delete'){j_log($s,'删除激活码',$row['product'].' · '.$row['mask']);unset($s['codes'][$id]);return ['ok'=>true];}
    else fail('接口不存在',404);
    $row['version']++;j_log($s,['unbind'=>'移除设备绑定','disable'=>'禁用激活码','enable'=>'启用激活码'][$action],$row['product'].' · '.$row['mask']);return ['ok'=>true];
}
function j_client_action(array &$s,string $action,array $b):array {
    j_sodium();j_rate($s,'client-'.$action,$action==='challenge'?120:120,300);
    foreach($s['challenges'] as $id=>$c)if($c['until']<time())unset($s['challenges'][$id]);
    if($action==='challenge'){
        if(count($s['challenges'])>=2000)fail('服务繁忙，请稍后重试',429);
        $purpose=$b['purpose']??'';if(!in_array($purpose,['activate','verify'],true))fail('校验用途无效',400);
        $product=j_product($b['product']??'');$device=text_field($b['device']??'',64,true);if(!preg_match('/^[a-f0-9]{64}$/',$device))fail('设备指纹应为 SHA-256 十六进制值',400);
        $public=text_field($b['publicKey']??'',48,true);$raw=base64_decode($public,true);if($raw===false||strlen($raw)!==32||base64_encode($raw)!==$public)fail('设备公钥格式不正确',400);
        $target=$purpose==='activate'?hash('sha256',j_code($b['code']??'')):text_field($b['licenseId']??'',32,true);
        if($purpose==='verify'&&!preg_match('/^[a-f0-9]{32}$/',$target))fail('许可证编号格式错误',400);
        $id=bin2hex(random_bytes(24));$until=time()+120;
        $message=json_encode(['protocol'=>'yuxuan-license-v1','challenge'=>$id,'purpose'=>$purpose,'product'=>$product,'device'=>$device,'publicKey'=>$public,'target'=>$target,'until'=>$until],JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR);
        $s['challenges'][$id]=['message'=>$message,'until'=>$until,'purpose'=>$purpose,'product'=>$product,'device'=>$device,'publicKey'=>$public,'target'=>$target,'name'=>text_field($b['deviceName']??'',120)];
        return ['challenge'=>$id,'message'=>base64_encode($message),'until'=>$until];
    }
    if(!in_array($action,['activate','verify'],true))fail('接口不存在',404);
    $id=text_field($b['challenge']??'',48,true);$c=$s['challenges'][$id]??null;
    if(!$c)fail('校验请求已过期或已使用，请重新获取',403);unset($s['challenges'][$id]);
    $signature=base64_decode(text_field($b['signature']??'',100,true),true);
    if($c['purpose']!==$action||$signature===false||strlen($signature)!==64||!sodium_crypto_sign_verify_detached($signature,$c['message'],base64_decode($c['publicKey'],true)))fail('设备签名校验失败',403);
    $license=null;if($action==='activate'){foreach($s['codes'] as $key=>$row)if(hash_equals($row['codeHash'],$c['target'])){$license=$key;break;}}elseif(isset($s['codes'][$c['target']]))$license=$c['target'];
    if($license===null)fail('激活码或许可证无效',403);$row=&$s['codes'][$license];
    if($row['product']!==$c['product']||!$row['enabled']||($row['expires']!==null&&$row['expires']<=time()))fail('授权无效、已到期或已禁用',403);
    if($row['binding']===null){if($action!=='activate')fail('设备绑定已被移除，请重新激活',403);$row['binding']=['device'=>$c['device'],'publicKey'=>$c['publicKey'],'name'=>$c['name'],'date'=>date(DATE_ATOM)];$row['version']++;j_log($s,'首次绑定设备',$row['product'].' · '.$row['mask']);}
    elseif(!hash_equals($row['binding']['device'],$c['device'])||!hash_equals($row['binding']['publicKey'],$c['publicKey']))fail('该激活码已绑定其他设备',409);
    $row['lastSeen']=date(DATE_ATOM);j_keys($s);
    $payload=json_encode(['protocol'=>'yuxuan-license-v1','licenseId'=>$license,'product'=>$row['product'],'device'=>$c['device'],'publicKey'=>$c['publicKey'],'version'=>$row['version'],'challenge'=>$id,'issued'=>time(),'until'=>min(time()+180,$row['expires']??PHP_INT_MAX),'expires'=>$row['expires']],JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR);
    $secret=base64_decode($s['secret'],true);
    $result=['payload'=>base64_encode($payload),'signature'=>base64_encode(sodium_crypto_sign_detached($payload,$secret))];
    if(in_array($row['product'],j_offline_products(),true)){
        $offline=json_encode(['protocol'=>'yuxuan-offline-license-v1','licenseId'=>$license,'product'=>$row['product'],'device'=>$c['device'],'publicKey'=>$c['publicKey'],'version'=>$row['version'],'challenge'=>$id,'issued'=>time(),'expires'=>$row['expires']],JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR);
        $result['offlinePayload']=base64_encode($offline);
        $result['offlineSignature']=base64_encode(sodium_crypto_sign_detached($offline,$secret));
    }
    return $result;
}
