<?php
require __DIR__.'/core.php';j_headers();header('Content-Type: application/json; charset=utf-8');
function j_reply(array $result):void {$status=$result['status']??200;unset($result['status']);http_response_code($status);echo json_encode($result,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR);exit;}
try{
    $action=(string)($_GET['action']??'session');$method=$_SERVER['REQUEST_METHOD'];
    if($action==='capabilities'&&$method==='GET')j_reply(['protocol'=>'yuxuan-license-v1','offlineProtocol'=>'yuxuan-offline-license-v1','offlineProducts'=>j_offline_products()]);
    if(in_array($action,['challenge','activate','verify'],true)){
        if($method!=='POST')fail('仅支持 POST',405);
        $raw=file_get_contents('php://input',false,null,0,16385);if(strlen($raw)>16384)fail('请求内容过大',413);
        $b=json_decode($raw,true);if(!is_array($b))fail('请求 JSON 无效',400);
        j_reply(j_state(function(&$s)use($action,$b){return j_client_action($s,$action,$b);}));
    }
    j_session();
    if($action==='session'&&$method==='GET')j_reply(['authenticated'=>j_authenticated(),'initialized'=>j_account()!==null,'csrf'=>$_SESSION['csrf']]);
    if($method!=='POST')fail('仅支持 POST',405);j_csrf();
    $raw=file_get_contents('php://input',false,null,0,16385);if(strlen($raw)>16384)fail('请求内容过大',413);$b=json_decode($raw,true);if(!is_array($b))fail('请求 JSON 无效',400);
    if($action==='login'){
        $account=j_account();if(!$account)fail('请先在 /linqing/ 创建博客管理员，再使用其密码登录',409);
        j_reply(j_state(function(&$s)use($account,$b){
            j_rate($s,'login',6,900);$password=$b['password']??'';
            if(!is_string($password)||strlen($password)>72||!password_verify($password,$account['hash']))fail('密码不正确',401);
            unset($s['rates'][hash('sha256','login:'.($_SERVER['REMOTE_ADDR']??''))]);session_regenerate_id(true);$_SESSION['licenseUser']=$account['username'];$_SESSION['licenseVersion']=$account['version'];$_SESSION['last']=time();$_SESSION['csrf']=bin2hex(random_bytes(32));j_log($s,'管理员登录');return ['ok'=>true,'csrf'=>$_SESSION['csrf']];
        }));
    }
    j_auth();
    if($action==='logout'){$_SESSION=[];session_destroy();j_reply(['ok'=>true]);}
    if(!in_array($action,['list','generate','unbind','disable','enable','delete'],true))fail('接口不存在',404);
    j_reply(j_state(function(&$s)use($action,$b){return j_admin_action($s,$action,$b);}));
}catch(Throwable $e){$status=$e instanceof RuntimeException&&$e->getCode()>=400&&$e->getCode()<600?$e->getCode():500;if($status===500)error_log('Activation service: '.$e->getMessage());j_reply(['error'=>$status===500?'服务器处理失败，请检查 PHP 扩展、目录权限或错误日志':$e->getMessage(),'status'=>$status]);}
