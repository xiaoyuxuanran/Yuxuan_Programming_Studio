
'use strict'

/**
 * Execute the user's code.
 * Just a quick and dirty eval.  No checks for infinite loops, etc.
 */
function runJS() {
    var code = Blockly.Generator.workspaceToCode('JavaScript');
    try {
        eval(code);
    } catch (e) {
        alert('Program error:\n' + e);
    }
}

/**
 * Backup code blocks to localStorage.
 */
function backup_blocks() {
    var xml = Blockly.Xml.workspaceToDom(Mixly.Editor.blockEditor);
    xml = Blockly.Xml.domToText(xml);
    var mixlyVersion = "Mixly 2.0";
    if (Mixly.Config.SOFTWARE?.version) {
        mixlyVersion = Mixly.Config.SOFTWARE.version;
    }
    if (document.getElementById("boards-type")) {
        xml = xml.replace("<xml xmlns=\"https://developers.google.com/blockly/xml\"", "<xml version=\"" + mixlyVersion + "\" board=\"" + $('#boards-type').find("option:selected").text() + "\" xmlns=\"http://www.w3.org/1999/xhtml\"");
    } else {
        xml = xml.replace("<xml xmlns=\"https://developers.google.com/blockly/xml\"", "<xml version=\"" + mixlyVersion + "\" board=\"all\" xmlns=\"http://www.w3.org/1999/xhtml\"");
    }

    if ('localStorage' in window && window['localStorage'] != null) {
        window.localStorage.setItem(Mixly.Config.BOARD.boardType, xml);
        window.localStorage.setItem(Mixly.Config.BOARD.boardType + ".openedPath", Mixly.Title.getFilePath());
    } else {
        //当同时打开打开两个以上（含两个）的Mixly窗口时，只有第一个打开的窗口才有window.localStorage对象，怀疑是javafx的bug.
        //其他的窗口得通过java写cache文件来实现，否则这些窗口在普通、高级视图中进行切换时，无法加载切换之前的块
        //JSFuncs.saveToLocalStorageCache(xml);
    }

    if ('localStorage' in window && window['localStorage'] != null && Mixly.Editor.mainEditor.selected === 'CODE') {
        window.localStorage.setItem(Mixly.Config.BOARD.boardType + ".code", Mixly.Editor.codeEditor.getValue());
        window.localStorage.setItem(Mixly.Config.BOARD.boardType + ".loadCode", "true");
    } else {
        window.localStorage.setItem(Mixly.Config.BOARD.boardType + ".loadCode", "false");
    }
}

function clear_blocks_from_storage() {
    var itl = setInterval(function () {
        if (window) {
            if ('localStorage' in window && window['localStorage'] != null && window.localStorage[Mixly.Config.BOARD.boardType]) {
                window.localStorage.removeItem(Mixly.Config.BOARD.boardType);
            }
            Mixly.Editor.blockEditor.clear();
            clearInterval(itl);
        }
    }, 200);
}

/**
 * Restore code blocks from localStorage.
 */
function restore_blocks() {
    const {
        Config,
        Electron = {},
        Web = {},
        Modules,
        Env,
        Drag,
        Editor,
        Boards,
        Title
    } = Mixly;
    const { BOARD } = Config;
    if (!('localStorage' in window && window['localStorage'] != null)) {
        return;
    }
    if (window.localStorage[BOARD.boardType + '.filePath'] && Env.isElectron) {
        const { File } = Electron;
        File.openFile(window.localStorage[BOARD.boardType + '.filePath']);
        window.localStorage[BOARD.boardType + '.filePath'] = '';
    } else if (window.localStorage[BOARD.boardType]) {
        let xml;
        try {
            xml = $(window.localStorage[BOARD.boardType])[0];
            if ($("#boards-type").length) {
                const boardNameList = window.localStorage[BOARD.boardType].match(/(?<=board[\s]*=[\s]*\")[^\n\"]+(?=\")/g);
                let boardName = boardNameList.length? boardNameList[0] : '';
                if (BOARD.boardName
                 && boardName !== BOARD.boardName
                 && BOARD.board
                 && BOARD.board[BOARD.boardName]) {
                    boardName = BOARD.boardName;
                }
                Boards.setSelectedBoard(boardName);
                profile['default'] = profile[boardName] ?? profile['default'];
            }
            Blockly.Xml.domToWorkspace(xml, Editor.blockEditor);
            Editor.blockEditor.scrollCenter();
        } catch (e) {
            Editor.blockEditor.clear();
            console.log(e);
            clear_blocks_from_storage();
        }
        if (window.localStorage[BOARD.boardType + ".loadCode"]
            && window.localStorage[BOARD.boardType + ".loadCode"] == "true") {
            if (window.localStorage[BOARD.boardType + ".code"]) {
                Editor.mainEditor.drag.full('NEGATIVE');
                Editor.codeEditor.setValue(window.localStorage[BOARD.boardType + ".code"], -1);
            }
        }
        if (window.localStorage[BOARD.boardType + ".openedPath"]
            && window.localStorage[BOARD.boardType + ".openedPath"] !== 'null'
            && Env.isElectron) {
            const filePath = window.localStorage[BOARD.boardType + ".openedPath"];
            const { File } = Electron;
            const { path } = Modules;
            File.openedFilePath = filePath;
            File.workingPath = path.dirname(filePath);
            Title.updeteFilePath(File.openedFilePath);
        }
    }
    const $loading = $('.loading');
    const toolboxWidth = $('.blocklyToolboxDiv').width();
    $loading.children('.left-div').animate({
      width: toolboxWidth + 'px'
    }, () => {
        $loading.fadeOut("fast", () => {
            $loading.remove();
        });
    });
}

/**
 * Save blocks to local file.
 * better include Blob and FileSaver for browser compatibility
 */
function save() {
    var xml = Blockly.Xml.workspaceToDom(Mixly.Editor.blockEditor);
    var data = Blockly.Xml.domToText(xml);

    // Store data in blob.
    // var builder = new BlobBuilder();
    // builder.append(data);
    // saveAs(builder.getBlob('text/plain;charset=utf-8'), 'blockduino.xml');
    console.log("saving blob");
    var blob = new Blob([data], { type: 'text/xml' });
    var fn = 'mixly.mix';
    saveAs(blob, fn);
}

/**
 * open serial modal
 */
async function openSerialModal() {
    await serialRead(deviceObj);
}

/**
 * Load blocks from local file.
 */
function load(event) {
    var files = event.target.files;
    // Only allow uploading one file.
    if (files.length != 1) {
        return;
    }

    // FileReader
    var reader = new FileReader();
    reader.onloadend = function (event) {
        var target = event.target;
        // 2 == FileReader.DONE
        if (target.readyState == 2) {
            try {
                var xml = Blockly.Xml.textToDom(target.result);
            } catch (e) {
                alert('Error parsing XML:\n' + e);
                return;
            }
            var count = Mixly.Editor.blockEditor.getAllBlocks().length;
            if (count && confirm('Replace existing blocks?\n"Cancel" will merge.')) {
                Mixly.Editor.blockEditor.clear();
            }
            Blockly.Xml.domToWorkspace(xml, Mixly.Editor.blockEditor);
            Mixly.Editor.blockEditor.scrollCenter();
        }
        // Reset value of input after loading because Chrome will not fire
        // a 'change' event if the same file is loaded again.
        document.getElementById('load').value = '';
    };
    reader.readAsText(files[0]);
}

/**
 * Discard all blocks from the workspace.
 */
function discard() {
    var count = Mixly.Editor.blockEditor.getAllBlocks().length;
    if (count < 2 || window.confirm('Delete all ' + count + ' blocks?')) {
        Mixly.Editor.blockEditor.clear();
    }
}

/*
 * auto save and restore blocks
 */
function auto_save_and_restore_blocks() {
    if (window.YuxuanDesktopRecovery) return;
    // Restore saved blocks in a separate thread so that subsequent
    // initialization is not affected from a failed load.
    window.setTimeout(restore_blocks, 200);
    // Hook a save function onto unload.
    bindEvent(window, 'unload', backup_blocks);
    // tabClick(selected);
    //$('.loading').remove();
    
    //Mixly.Editor.blockEditor.clear();
    // Init load event.
    //var loadInput = document.getElementById('load');
    //loadInput.addEventListener('change', load, false);
    //document.getElementById('fakeload').onclick = function () {
    //    loadInput.click();
    //};
}

/**
 * Bind an event to a function call.
 * @param {!Element} element Element upon which to listen.
 * @param {string} name Event name to listen to (e.g. 'mousedown').
 * @param {!Function} func Function to call when event is triggered.
 *     W3 browsers will call the function with the event object as a parameter,
 *     MSIE will not.
 */
function bindEvent(element, name, func) {
    if (element.addEventListener) {  // W3C
        element.addEventListener(name, func, false);
    } else if (element.attachEvent) {  // IE
        element.attachEvent('on' + name, func);
    }
}

//loading examples via ajax
var ajax;
function createAJAX() {
    if (window.ActiveXObject) { //IE
        try {
            return new ActiveXObject("Msxml2.XMLHTTP");
        } catch (e) {
            try {
                return new ActiveXObject("Microsoft.XMLHTTP");
            } catch (e2) {
                return null;
            }
        }
    } else if (window.XMLHttpRequest) {
        return new XMLHttpRequest();
    } else {
        return null;
    }
}

function onSuccess() {
    if (ajax.readyState == 4) {
        if (ajax.status == 200) {
            try {
                var xml = Blockly.Xml.textToDom(ajax.responseText);
            } catch (e) {
                alert('Error parsing XML:\n' + e);
                return;
            }
            var count = Mixly.Editor.blockEditor.getAllBlocks().length;
            if (count && confirm('Replace existing blocks?\n"Cancel" will merge.')) {
                Mixly.Editor.blockEditor.clear();
            }
            Blockly.Xml.domToWorkspace(xml, Mixly.Editor.blockEditor);
            Mixly.Editor.blockEditor.scrollCenter();
        } else {
            //alert("Server error");
        }
    }
}

function load_by_url(uri) {
    ajax = createAJAX();
    if (!ajax) {
        alert('Not compatible with XMLHttpRequest');
        return 0;
    }
    if (ajax.overrideMimeType) {
        ajax.overrideMimeType('text/xml');
    }

    ajax.onreadystatechange = onSuccess;
    ajax.open("GET", uri, true);
    ajax.send("");
}

function uploadCode(code, callback) {
    var target = document.getElementById('content_arduino');
    var spinner = new Spinner().spin(target);

    var url = "http://127.0.0.1:8080/";
    var method = "POST";

    // You REALLY want async = true.
    // Otherwise, it'll block ALL execution waiting for server response.
    var async = true;

    var request = new XMLHttpRequest();

    request.onreadystatechange = function () {
        if (request.readyState != 4) {
            return;
        }

        spinner.stop();

        var status = parseInt(request.status); // HTTP response status, e.g., 200 for "200 OK"
        var errorInfo = null;
        switch (status) {
            case 200:
                break;
            case 0:
                errorInfo = "code 0\n\nCould not connect to server at " + url + ".  Is the local web server running?";
                break;
            case 400:
                errorInfo = "code 400\n\nBuild failed - probably due to invalid source code.  Make sure that there are no missing connections in the blocks.";
                break;
            case 500:
                errorInfo = "code 500\n\nUpload failed.  Is the Arduino connected to USB port?";
                break;
            case 501:
                errorInfo = "code 501\n\nUpload failed.  Is 'ino' installed and in your path?  This only works on Mac OS X and Linux at this time.";
                break;
            default:
                errorInfo = "code " + status + "\n\nUnknown error.";
                break;
        };

        callback(status, errorInfo);
    };

    request.open(method, url, async);
    request.setRequestHeader("Content-Type", "text/plain;charset=UTF-8");
    request.send(code);
}

function uploadClick() {
    var code = document.getElementById('textarea_arduino').value;

    alert("Ready to upload to Arduino.\n\nNote: this only works on Mac OS X and Linux at this time.");

    uploadCode(code, function (status, errorInfo) {
        if (status == 200) {
            alert("Program uploaded ok");
        } else {
            alert("Error uploading program: " + errorInfo);
        }
    });
}

function resetClick() {
    var code = "void setup() {} void loop() {}";

    uploadCode(code, function (status, errorInfo) {
        if (status != 200) {
            alert("Error resetting program: " + errorInfo);
        }
    });
}

'use strict';

/** Create a namespace for the application. */

goog.require('Blockly.Generator');
try {
    goog.require('Blockly.Python');
} catch (e) {
    goog.require('Blockly.Arduino');
}

var mixlyjs = mixlyjs || {};
mixlyjs.hex = "";

mixlyjs.createFn = function () {
    if (document.getElementById("username") === null) {
        mixlyjs.discardAllBlocks();
    } else {
        //$("#opModal").load(mixlyjs.modalPagesPath + "create_new_project.html");
        $('#opModal').modal('show');
    }
};

/**
 *clear the mainWorkSpace 
 */
mixlyjs.discardAllBlocks = function () {
    Mixly.Editor.blockEditor.clear();
};

mixlyjs.operateModal = function (action) {
    $("#opModal").modal(action);
};

mixlyjs.translateQuote = function (str, trimEscaped) {
    var xml = "";
    var hasComleteAngleBracket = true;
    var lenStr = str.length;
    for (var i = 0; i < lenStr; i++) {
        if (str[i] === "<") {
            hasComleteAngleBracket = false;
        } else if (str[i] === ">") {
            hasComleteAngleBracket = true;
        }

        if (trimEscaped === true
            && hasComleteAngleBracket === false
            && i + 1 < lenStr
            && str[i] === "\\"
            && str[i + 1] === '"') {
            i += 1;
        }

        if (trimEscaped === false
            && hasComleteAngleBracket === false
            && i > 0
            && str[i - 1] !== "\\"
            && str[i] === '"') {
            xml += "\\";
        }
        xml += str[i];
    }
    return xml;
}

mixlyjs.getBoardFromXml = function (xml) {
    if (xml.indexOf("board=\"") === -1) {
        var idxa = xml.indexOf("board=\\\"") + 7;
        var idxb = xml.indexOf("\"", idxa + 1);
        if (idxa !== -1 && idxb !== -1 && idxb > idxa)
            return xml.substring(idxa + 1, idxb - 1);
    } else {
        var idxa = xml.indexOf("board=\"") + 6;
        var idxb = xml.indexOf("\"", idxa + 1);
        if (idxa !== -1 && idxb !== -1 && idxb > idxa)
            return xml.substring(idxa + 1, idxb);
    }
    return undefined;
}

/*处理ardunio板子之间的互相切换*/
mixlyjs.changeBoardName = function (xmlContent, cb) {
    var itl = setInterval(function () {
        if (compilerflasher.loadedBoardList == true) {

            var boardName = mixlyjs.getBoardFromXml(xmlContent);
            if (boardName !== undefined) {
                var boardProfileName = boardName.replace(/\[.*?\]/, "");
                if (profile[boardProfileName] === undefined) {
                    alert("错误：确保板子名称和boardList里的一致！");
                    clearInterval(itl);
                    return;
                }
                $("#cb_cf_boards").val(boardName);
                profile['default'] = profile[boardProfileName];
            } else {
                profile['default'] = profile[$("#cb_cf_boards").find("option:selected").text().replace(/\[.*?\]/, "")];
            }
            cb();
            clearInterval(itl);
        }
    }, 200);

}

mixlyjs.renderXml = function (xmlContent) {
    var boardType;
    try {
        boardType = xmlContent.match(/(?<=board[\s]*=[\s]*\")[^\n\"]+(?=\")/g);
        if (document.getElementById("boards-type")) {
            //console.log(boardType);
            var form = layui.form;
            if (boardType[0].indexOf('@') != -1) {
                boardType[0] = boardType[0].substring(boardType[0].indexOf('@') + 1, boardType[0].length);
            } else if (boardType[0].indexOf('/') != -1) {
                boardType[0] = boardType[0].substring(boardType[0].indexOf('/') + 1, boardType[0].length);
            }
            var count = $("#boards-type option").length;
            for (var i = 0; i < count; i++) {
                if ($("#boards-type").get(0).options[i].text == boardType[0]) {
                    $("#boards-type").get(0).options[i].selected = true;
                    break;
                }
            }
            form.render();
            if (profile[$("#boards-type").find("option:selected").text()] != undefined) {
                profile['default'] = profile[$("#boards-type").find("option:selected").text()];
            }
        }
    } catch (e) {
        console.log(e);
    }
    var oldCode = ""
    var oldBlock = "";
    if (Mixly.Env.isElectron)
        oldBlock = Mixly.Electron.File.getMix("project");
    else
        oldBlock = mixlyjs.getXmlContent("project");
    oldCode = editor.getValue();
    var select = false;
    var data = "";
    var output_data = "";
    let xmlData = xmlContent;
    try {
        xmlData = xmlData.replace(/varid\=\"[^\"]+\"/g, "");
        xmlData = xmlData.replace(/id\=\"[^\"]+\"/g, "");
    } catch (error) {
        console.log(error);
    }
    try {
        var xml = Blockly.utils.xml.textToDom(xmlContent);
        Mixly.Editor.blockEditor.clear();
        Blockly.Xml.domToWorkspace(xml, Mixly.Editor.blockEditor);
        Mixly.Editor.blockEditor.scrollCenter();
        Blockly.hideChaff();
    } catch (e) {
        try {
            var xml = Blockly.utils.xml.textToDom(xmlData);
            Mixly.Editor.blockEditor.clear();
            Blockly.Xml.domToWorkspace(xml, Mixly.Editor.blockEditor);
            Mixly.Editor.blockEditor.scrollCenter();
            Blockly.hideChaff();
        } catch (e) {
            boardType = xmlContent.match(/(?<=board[\s]*=[\s]*\")[^\n\"]+(?=\")/g);
            alert("代码面向" + boardType[0] + "板卡开发，不支持本板卡")
            var xml = Blockly.utils.xml.textToDom(oldBlock);
            Mixly.Editor.blockEditor.clear();
            Blockly.Xml.domToWorkspace(xml, Mixly.Editor.blockEditor);
            Mixly.Editor.blockEditor.scrollCenter();
            Blockly.hideChaff();
            editor.setValue(oldCode, -1);
            console.log(e);
            return false;
        }
    }
    return true;
};
mixlyjs.renderIno = function (xmlContent) {
    document.getElementById('changemod-btn').value = 0;
    document.getElementById('changemod-btn').textContent = Blockly.Msg.MSG['tab_blocks'];
    document.getElementById('changemod-btn').className = "icon-puzzle";
    tabClick('arduino');
    editor.setValue(xmlContent, -1);
};
mixlyjs.isArduino = function (board) {
    return board.indexOf("Arduino") !== -1;
}
mixlyjs.isMicrobitjs = function (board) {
    return board === "microbit[js]";
}
mixlyjs.isMicrobitpy = function (board) {
    return board === "microbit[py]";
}
mixlyjs.isMixpy = function (board) {
    return board === "mixpy";
}
mixlyjs.isSameTypeBoard = function (boarda, boardb) {
    if (boarda.indexOf("Arduino") !== -1 && boardb.indexOf("Arduino") !== -1)
        return true;
    else if (boarda == boardb)
        return true;
    else
        return false;
}
mixlyjs.getFileSuffix = function (fname) {
    return fname.substring(fname.lastIndexOf(".") + 1);
}

mixlyjs.loadServer = function () {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == 'id') {
            var id = pair[1];
        }
    }
    $.post("../../down_file.php", { "id": id }, function (res) {
        if (res.code === 50) {
            layer.msg(res.msg);
            setTimeout("window.location.href='../../index.html'", 1000);
        } else {
            var index = parent.layer.getFrameIndex(window.name);
            parent.layer.close(index);
            var text = res.data;
            var name = res.name;
            var filesuffix = name.split(".")[1];
            if (filesuffix === "xml" || filesuffix === "mix") {
                var newboard = mixlyjs.getBoardFromXml(text)
                if (newboard !== undefined) {
                    mixlyjs.renderXml(text);
                } else {
                    alert("Error:could not read board from xml!!");
                }
            } else if (filesuffix === "py") {
                mixlyjs.renderIno(text);
            } else {
                alert("Invalid file type! (.ino|.xml|.mix|.js|.py|.hex file supported)");
                return;
            }

        }
    }, 'json');
}

function openNew(id) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == 'type') {
            var type = pair[1];
        }
    }
    if (type == 'python') {
        var url = "apps/mixly/index_skulpt_board_mixpy.html?id=";
    } else if (type == 'circuit') {
        var url = "apps/mixly/index_board_CircuitPython[ESP32S2_MixGoCE].html?id=";
    }
    window.open(url + id);
}

function decode(s) {
    let newStr = s;
    try {
        newStr = newStr.replace(/(?<=id\=\")[^\"]+(?=\")/g, (word) => {
            if (word)
                return word.replaceAll('%', '');
            else
                return word;
        });
        return unescape(newStr.replace(/\\(u[0-9a-fA-F]{4})/gm, '%$1'));
    } catch (error) {
        console.log(error);
        return s;
    }
}

function loadFile() {
    const loadFileDom = $('<input></input>');
    const { openFilters } = Mixly.MFile;
    let openFiltersStr = '';
    for (let i of openFilters)
        openFiltersStr += '.' + i + ',';
    openFiltersStr = openFiltersStr.substring(0, openFiltersStr.length - 1);
    loadFileDom.attr({
        id: 'load-file',
        type: 'file',
        name: 'load-file',
        accept: openFiltersStr,
        onchange: 'getFile(this)'
    });
    loadFileDom.css('display', 'none');
    $('#load-file').remove();
    $('body').append(loadFileDom);
    return document.getElementById("load-file").click();
}

function getFile(input) {
    var files = input.files;
    if (files[0].size > 10 * 1024 * 1024) { //限制上传文件的 大小,此处为10M
        alert('你选择的文件太大了！');
        $('#load-file').remove();
        return false;
    }
    var resultFile = input.files[0];
    // 如果文件存在
    if (resultFile) {
        var reader = new FileReader();
        reader.readAsText(resultFile);
        reader.onload = function (e) {
            var fileContent = e.target.result;
            var text = mixlyjs.translateQuote(fileContent, true);
            var filesuffix = files[0].name.split(".")[files[0].name.split(".").length - 1];
            $('#load-file').remove();
            if (filesuffix === "xml" || filesuffix === "mix") {
                var newboard = mixlyjs.getBoardFromXml(text);
                if (newboard !== undefined) {
                    mixlyjs.renderXml(decode(text));
                } else {
                    alert("Error:could not read board from xml!!");
                }
            } else if (filesuffix === "py" || filesuffix === "ino") {
                mixlyjs.renderIno(text);
            } else if (filesuffix === "hex") {
                loadHex("main.py", text);
            } else {
                alert("Invalid file type! (.ino|.xml|.mix|.js|.py|.hex file supported)");
                return;
            }
        };
    };
}

mixlyjs.loadLocalFile = function () {
    // Create event listener function
    var parseInputXMLfile = function (e) {
        var files = this.files;
        var reader = new FileReader();
        reader.onload = function () {
            var text = mixlyjs.translateQuote(reader.result, true);
            var filesuffix = files[0].name.split(".")[files[0].name.split(".").length - 1];

            if (filesuffix === "xml" || filesuffix === "mix") {
                var newboard = mixlyjs.getBoardFromXml(text);
                if (newboard !== undefined) {
                    mixlyjs.renderXml(decode(text));
                } else {
                    alert("Error:could not read board from xml!!");
                }
            } else if (filesuffix === "py") {
                mixlyjs.renderIno(text);
            } else if (filesuffix === "hex") {
                loadHex("main.py", text);
            } else {
                alert("Invalid file type! (.ino|.xml|.mix|.js|.py|.hex file supported)");
                return;
            }
        };
        reader.readAsText(files[0]);
    };
    // Create once invisible browse button with event listener, and click it
    var selectFile = document.getElementById('select_file');
    if (selectFile != null) {
        $("#select_file").remove();
        $("#select_file_wrapper").remove();
        selectFile = document.getElementById('select_file');
    }
    if (selectFile == null) {
        var selectFileDom = document.createElement('INPUT');
        selectFileDom.type = 'file';
        selectFileDom.id = 'select_file';

        var selectFileWrapperDom = document.createElement('DIV');
        selectFileWrapperDom.id = 'select_file_wrapper';
        selectFileWrapperDom.style.display = 'none';
        selectFileWrapperDom.appendChild(selectFileDom);

        document.body.appendChild(selectFileWrapperDom);
        selectFile = document.getElementById('select_file');
        //$("body").on('change', '#select_file', parseInputXMLfile);
        $("#select_file").change(parseInputXMLfile);
    }
    selectFile.click();
};
mixlyjs.down_file = function () {
    $.post("../../down_file.php", { "type": 1 }, function (res) {
    }, 'json');

}

mixlyjs.downloadfile = function (type) {
    if (type == 'python') {
        layui.use('layer', function () {
            var layer = layui.layer;
            var $ = layui.jquery;
            layer.open({
                type: 2,
                title: "云端文件",
                skin: 'layui-layer-rim', //加上边框
                area: ['500px', '400px'], //宽高
                content: "../../download.php?type=python",
            });

            return false;
        })
    } else {
        layui.use('layer', function () {
            var layer = layui.layer;
            var $ = layui.jquery;
            layer.open({
                type: 2,
                title: "下载文件",
                skin: 'layui-layer-rim', //加上边框
                area: ['500px', '400px'], //宽高
                content: "../../download.php?type=circuit",
            });

            return false;
        })
    }
};

mixlyjs.viewfile = function (type) {
    layui.use('layer', function () {
        var layer = layui.layer;
        var $ = layui.jquery;
        layer.open({
            type: 2,
            title: "资源",
            skin: 'layui-layer-rim', //加上边框
            area: ['500px', '400px'], //宽高
            content: "../../../viewfile.html",
        });
        return false;
    });
};

mixlyjs.getCodeContent = function () {
    return Mixly.MFile.getCode();
};

mixlyjs.getXmlContent = function (xmlType) {
    var xmlCodes = Blockly.Xml.domToText(Blockly.Xml.workspaceToDom(Mixly.Editor.blockEditor));
    var mixlyVersion = "Mixly 2.0";
    if (Mixly.Config.BOARD?.software?.version) {
        mixlyVersion = Mixly.Config.BOARD.software.version;
    }
    if (xmlType === "project") {
        var boardName = $("#cb_cf_boards").val();
        xmlCodes = xmlCodes.replace("<xml", "<xml version=\\\"" + mixlyVersion + "\\\" board=\\\"" + boardName + "\\\"");
    } else if (xmlType === "lib")
        xmlCodes = xmlCodes.replace("<xml", "<xml version=\\\"" + mixlyVersion + "\\\" board=\\\"" + "mylib" + "\\\"");
    return xmlCodes.substring(1, xmlCodes.length - 1);
};

/**
 * Creates an XML file containing the blocks from the Blockly workspace and
 * prompts the users to save it into their local file system.
 */
mixlyjs.saveXmlFileAs = function () {
    var xmlCodes = mixlyjs.getXmlContent("project");
    var blob = new Blob(
        [xmlCodes],
        { type: 'text/plain;charset=utf-8' });
    saveAs(blob, "Mixgo.xml");
};

mixlyjs.saveInoFileAs = function (f) {
    var xmlCodes = mixlyjs.getCodeContent();
    var fn = 'code.ino';
    var blob = new Blob(
        [xmlCodes],
        { type: 'text/plain;charset=utf-8' });
    saveAs(blob, fn);
};

mixlyjs.savePyFileAs = function (f) {
    var xmlCodes = mixlyjs.getCodeContent();
    var fn = 'code.py';
    var blob = new Blob(
        [xmlCodes],
        { type: 'text/plain;charset=utf-8' });
    saveAs(blob, fn);
};

mixlyjs.saveCommonFileAs = function (fname, fcontent) {
    var blob = new Blob(
        [fcontent],
        { type: 'text/plain;charset=utf-8' });
    saveAs(blob, fname);
};

mixlyjs.compileMicrobitPy = function () {
    var fn = 'code.hex';
    mixlyjs.saveCommonFileAs(fn, doDownload())
}