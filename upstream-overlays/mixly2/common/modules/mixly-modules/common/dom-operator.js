goog.loadJs('common', () => {

goog.require('layui');
goog.require('Mixly.Config');
goog.require('Mixly.XML');
goog.require('Mixly.Env');
goog.require('Mixly.Msg');
goog.provide('Mixly.DomOperator');

const {
    DomOperator,
    Config,
    XML,
    Env,
    Msg
} = Mixly;

const { BOARD, USER } = Config;

const { laytpl } = layui;

DomOperator.SerialDom = {
    times: 0,
    getTimes: () => {
        this.times = typeof this.times !== 'undefined' ? this.times + 1 : 0;
        if (this.times > 10) this.times = 0;
        return this.times;
    }
}

const { SerialDom } = DomOperator;

// 串口工具
class SerialDomGenerator {
    constructor(serialConfig, shade, lang) {
        this.mark = SerialDom.getTimes();
        this.id = this.getId();
        this.filter = this.getFilter();
        this.lang = lang;
        this.shade = shade;
        this.config = this.getConfig(serialConfig);
        this.htmlTemplatePath = Env.templatePath + '/serial-tool.html';
        this.htmlStr = this.getHtmlStr();
        this.generateDom();
        this.destroyed = false;
        this.width = null;
        this.height = null;
        this.prevPort = null;
        this.nowPort = null;
    }

    getConfig(config) {
        let _defaultConfig = {
            "baudRates": 9600,
            "ctrlCBtn": false,
            "ctrlDBtn": false,
            "receiveStr": true,
            "scroll": true,
            "sendStr": true,
            "sendWith": "\\r\\n",
            "dtr": true,
            "rts": true,
            "pointNum": 100,
            "yMax": 100,
            "yMin": 0
        };
        return DomOperator.getConfig(config, _defaultConfig);
    }

    getHtmlStr() {
        this.htmlTemplate = goog.get(this.htmlTemplatePath);
        return laytpl(this.htmlTemplate).render({
            ...this.id,
            ...this.filter,
            baudRates: [ 9600, 19200, 28800, 38400, 57600, 115200 ],
            selectedBaud: this.config.baudRates,
            pointList: [ 50, 100, 150, 200, 250, 300 ],
            pointNum: this.config.pointNum,
            ctrlCBtn: this.config.ctrlCBtn,
            ctrlDBtn: this.config.ctrlDBtn,
            yMax: this.config.yMax,
            yMin: this.config.yMin,
            dtr: this.config.dtr ? 'checked' : '',
            rts: this.config.rts ? 'checked' : '',
            Msg: {
                monitor: Msg.Lang['串口监视器'],
                visualization: Msg.Lang['串口可视化'],
                serial: Msg.Lang['串口'],
                open: Msg.Lang['打开'],
                sendData: Msg.Lang['发送数据'],
                send: Msg.Lang['发送'],
                string: Msg.Lang['字符串'],
                input: Msg.Lang['请输入内容'],
                receiveData: Msg.Lang['接收数据'],
                scroll: Msg.Lang['滚屏'],
                clear: Msg.Lang['清空'],
                interrupt: Msg.Lang['中断'],
                reset: Msg.Lang['复位'],
                min: Msg.Lang['最小'],
                max: Msg.Lang['最大'],
                pointNum: Msg.Lang['点数']
            }
        });
    }


    generateDom() {
        let { formId } = this.id;
        let { formFilter } = this.filter;
        let serialDom = this;
        layui.use(['layer', 'form'], function () {
            let form = layui.form;
            let _divObj = document.createElement("div");
            _divObj.innerHTML = serialDom.htmlStr;
            _divObj.className = "layui-form layui-form-pane";
            _divObj.id = formId;
            _divObj.style.display = "none";
            _divObj.setAttribute("lay-filter", formFilter);
            document.body.appendChild(_divObj);
            form.render(null, formFilter);
        });
    }

    updateDom() {
        let { formId } = this.id;
        let { formFilter } = this.filter;
        let serialDom = this;
        layui.use(['layer', 'form'], function () {
            let form = layui.form;
            let _divObj = document.getElementById(formId);
            serialDom.htmlStr = serialDom.getHtmlStr();
            _divObj.innerHTML = serialDom.htmlStr;
            form.render(null, formFilter);
        });
    }

    getId() {
        let _id = {
            "pageId": `serial-page-${this.mark}`,
            "formId": `serial-${this.mark}`,
            "setDtrId": `serial-set-dtr-${this.mark}`,
            "setRtsId": `serial-set-rts-${this.mark}`,
            "selectPortId": `serial-selectport-${this.mark}`,
            "selectBaudId": `serial-selectbaud-${this.mark}`,
            "connectBtnId": `serial-connectbtn-${this.mark}`,
            "sendTypeId": `serial-sendtype-${this.mark}`,
            "sendId": `serial-send-${this.mark}`,
            "sendWithId": `serial-sendwith-${this.mark}`,
            "sendBtnId": `serial-sendbtn-${this.mark}`,
            "receiveTypeId": `serial-receivetype-${this.mark}`,
            "scrollId": `serial-scroll-${this.mark}`,
            "receiveId": `serial-receive-${this.mark}`,
            "clearBtnId": `serial-clearbtn-${this.mark}`,
            "ctrlCBtnId": `serial-interruptbtn-${this.mark}`,
            "ctrlDBtnId": `serial-resetbtn-${this.mark}`,
            "yMinId": `serial-ymin-${this.mark}`,
            "yMaxId": `serial-ymax-${this.mark}`,
            "pointNumId": `serial-pointnum-${this.mark}`,
            "chartSendTypeId": `serial-chartsendType-${this.mark}`,
            "chartSendId": `serial-chartsend-${this.mark}`,
            "chartSendWithId": `serial-chartsendWith-${this.mark}`,
            "chartSendBtnId": `serial-chartsendBtn-${this.mark}`,
            "dataDrawId": `serial-datadraw-${this.mark}`,
            "moveId": `serial-move-${this.mark}`
        }

        return _id;
    }

    getFilter() {
        let _filter = {
            "formFilter": `serial-filter-${this.mark}`,
            "setDtrFilter": `serial-set-dtr-filter-${this.mark}`,
            "setRtsFilter": `serial-set-rts-filter-${this.mark}`,
            "selectPortFilter": `serial-select-port-filter-${this.mark}`,
            "selectBaudFilter": `serial-select-baud-filter-${this.mark}`,
            "sendTypeFilter": `serial-send-type-filter-${this.mark}`,
            "sendWithFilter": `serial-send-with-filter-${this.mark}`,
            "chartSendTypeFilter": `serial-chart-send-type-filter-${this.mark}`,
            "tabFilter": `serial-tab-filter-${this.mark}`,
            "receiveTypeFilter": `serial-set-receive-type-filter-${this.mark}`,
            "scrollFilter": `serial-scroll-filter-${this.mark}`,
            "selectPointNumFilter": `serial-select-point-num-filter-${this.mark}`,
            "connectBtnFilter": `serial-connect-btn-filter-${this.mark}`
        }

        return _filter;
    }

    adjustSerialTool(layero, index) {
        const { pageId, moveId } = this.id;
        layero.css({
            minWidth: '350px',
            minHeight: '200px',
            maxWidth: '710px',
            maxHeight: '600px',
            borderRadius: '5px'
        });
        const nowHeight = $(window).height(),
        nowWidth = $(window).width();
        layero.css({
            left: (nowWidth - layero.width()) / 2 + "px",
            top: (nowHeight - layero.height()) / 2 + "px"
        });

        const serialPageDom = $('#' + pageId);
        serialPageDom.css({
            height: '100%',
            overflow: 'hidden',
            maxWidth: '710px',
            maxHeight: '600px',
            minWidth: '350px',
            minHeight: '200px',
            borderRadius: '8px'
        });
    }

    open(sucFunc = () => {}, endFunc = () => {}) {
        let serialDom = this;
        let nowHeight = $(window).height();
        let nowWidth = $(window).width();
        let pageArea = ["90%", "95%"];
        if (this.height && nowHeight > this.height && 100*this.height/nowHeight < 95)
            pageArea[1] = 100*this.height/nowHeight + '%';
        if (this.width && nowWidth > this.width && 100*this.width/nowWidth < 90)
            pageArea[0] = 100*this.width/nowWidth + '%';

        layui.use(['layer', 'form'], () => {
            let layer = layui.layer;
            let form = layui.form;
            let { selectPortId, formId, moveId, pageId, receiveId } = serialDom.id;
            let { formFilter } = serialDom.filter;
            let receiveDom = $('#' + receiveId);
            serialDom.tool = layer.open({
                type: 1,
                id: pageId,
                title: false,
                area: pageArea,
                shade: this.shade,
                closeBtn: 1,
                anim: 0,
                resize: true,
                fixed: true,
                move: $('#' + moveId),
                //content: this.getHtmlStr()[0],
                content: $('#' + formId),
                success: (layero, index) => {
                    layero.addClass('yuxuan-serial-dialog');
                    layero.find('.yuxuan-serial-close').off('click.yuxuan').on('click.yuxuan', (event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        serialDom.close();
                    });
                    receiveDom.val("");
                    form.render(null, formFilter);
                    serialDom.adjustSerialTool(layero, index);
                    sucFunc(serialDom);
                },
                end: () => {
                    $(".layui-layer-shade").remove();
                    endFunc(this.nowPort);
                },
                resizing: (layero) => {
                    let nowHeight = $(window).height();
                    let nowWidth = $(window).width();
                    layero.css({
                        width: layero.width()/nowWidth*100 + "%",
                        height: layero.height()/nowHeight*100 + "%"
                    });
                    $('#' + pageId).css('height', '100%');
                    this.width = layero[0].clientWidth;
                    this.height = layero[0].clientHeight;
                }
            });
        });
    }

    close() {
        layer.close(this.tool);
    }

    updateTool(serialConfig) {
        this.config = this.getConfig(serialConfig);
        const {
            setDtrId,
            setRtsId,
            selectPortId,
            selectBaudId,
            sendTypeId,
            sendWithId,
            receiveTypeId,
            scrollId,
            yMinId,
            yMaxId,
            pointNumId
        } = this.id;
        const { form } = layui;
        const setDtrDom = $('#' + setDtrId),
              setRtsDom = $('#' + setRtsId),
              selectPortDom = $('#' + selectPortId),
              selectBaudDom = $('#' + selectBaudId),
              sendTypeDom = $('#' + sendTypeId),
              sendWithDom = $('#' + sendWithId),
              receiveTypeDom = $('#' + receiveTypeId),
              scrollDom = $('#' + scrollId),
              yMinDom = $('#' + yMinId),
              yMaxDom = $('#' + yMaxId),
              pointNumDom = $('#' + pointNumId);
        const checkboxObj = {
            'dtr': setDtrDom,
            'rts': setRtsDom,
            'sendStr': sendTypeDom,
            'receiveStr': receiveTypeDom,
            'scroll': scrollDom
        };
        const selectObj = {
            'port': selectPortDom,
            'baudRates': selectBaudDom,
            'sendWith': sendWithDom,
            'yMin': yMinDom,
            'yMax': yMaxDom,
            'pointNum': pointNumDom
        };
        for (let i in checkboxObj) {
            if (typeof this.config[i] !== 'undefined') {
                const nowDom = checkboxObj[i];
                nowDom.prop('checked', this.config[i]);
            }
        }
        for (let i in selectObj) {
            if (typeof this.config[i] !== 'undefined') {
                const nowDom = selectObj[i];
                $(nowDom).val(this.config[i]);
            }
        }
        form.render();
    }

    formOnClick(type, filter, doFunc) {
        layui.use(['layer', 'form'], () => {
            let form = layui.form;
            form.on(type + "(" + filter + ")", (elem) => {
                const { selectPortFilter } = this.filter;
                if (filter === selectPortFilter) {
                    if (elem.value === this.nowPort) return;
                    this.prevPort = this.nowPort;
                    this.nowPort = elem.value;
                    doFunc(this.prevPort, this.nowPort, elem);
                } else {
                    doFunc(this.nowPort, elem);
                }
            });
        });
    }

    elementOnClick(type, filter, doFunc) {
        layui.use(['layer', 'element'], () => {
            let element = layui.element;
            element.on(type + "(" + filter + ")", (elem) => {
                doFunc(this.nowPort, elem);
            });
        });
    }

    btnOnClick(id, doFunc) {
        $('#' + id).off("click").click(() => {
            doFunc(this.nowPort);
        });
    }

    onClickSetDtr(doFunc) {
        let { setDtrFilter } = this.filter;
        this.formOnClick("checkbox", setDtrFilter, doFunc);
    }

    onClickSetRts(doFunc) {
        let { setRtsFilter } = this.filter;
        this.formOnClick("checkbox", setRtsFilter, doFunc);
    }

    onClickSendType(doFunc) {
        let { sendTypeFilter } = this.filter;
        this.formOnClick("checkbox", sendTypeFilter, doFunc);
    }

    onClickReceiveType(doFunc) {
        let { receiveTypeFilter } = this.filter;
        this.formOnClick("checkbox", receiveTypeFilter, doFunc);
    }

    onClickScroll(doFunc) {
        let { scrollFilter } = this.filter;
        this.formOnClick("checkbox", scrollFilter, doFunc);
    }

    onClickSelectPort(doFunc) {
        let { selectPortFilter } = this.filter;
        this.formOnClick("select", selectPortFilter, doFunc);
    }

    onClickSelectBaud(doFunc) {
        let { selectBaudFilter } = this.filter;
        this.formOnClick("select", selectBaudFilter, doFunc);
    }

    onClickSelectPointNum(doFunc) {
        let { selectPointNumFilter } = this.filter;
        this.formOnClick("select", selectPointNumFilter, doFunc);
    }

    onClickSelectSendWith(doFunc) {
        let { sendWithFilter } = this.filter;
        this.formOnClick("select", sendWithFilter, doFunc);
    }

    onClickTab(doFunc) {
        let { tabFilter } = this.filter;
        this.elementOnClick("tab", tabFilter, doFunc);
    }

    onClickConnectBtn(doFunc) {
        let { connectBtnId } =this.id;
        this.btnOnClick(connectBtnId, doFunc);
    }

    onClickSendBtn(doFunc) {
        let { sendBtnId } =this.id;
        this.btnOnClick(sendBtnId, doFunc);
    }

    onClickChartSendBtn(doFunc) {
        let { chartSendBtnId } =this.id;
        this.btnOnClick(chartSendBtnId, doFunc);
    }

    onClickCtrlCBtn(doFunc) {
        let { ctrlCBtnId } =this.id;
        if (!ctrlCBtnId) return;
        this.btnOnClick(ctrlCBtnId, doFunc);
    }

    onClickCtrlDBtn(doFunc) {
        let { ctrlDBtnId } =this.id;
        if (!ctrlDBtnId) return;
        this.btnOnClick(ctrlDBtnId, doFunc);
    }

    onClickClearBtn(doFunc) {
        let { clearBtnId } =this.id;
        this.btnOnClick(clearBtnId, doFunc);
    }

    destroy() {
        if (this.tool)
            layer.close(this.tool);
        let { formId } = this.id;
        $('#' + formId).remove();
        this.destroyed = true;
    }
}

SerialDom.generate = SerialDomGenerator;

DomOperator.LoaderDomGenerator = (mark, config) => {

}

class LoaderDomGenerator {
    constructor(mark, config) {
        this.mark = mark;
        this.config = this.getConfig(config);
    }

    getConfig(config) {
        let _defaultConfig = {
            title: '',
            cancel: function () {}
        };

        return DomOperator.getConfig(config, _defaultConfig);
    }

    btnOnClick(id, doFunc) {
        $(document).on('click', '#' + id, function() {
            doFunc();
        });
    }

    onClickCancel(doFunc) {

    }

    chanageTitle(title) {

    }

    destroy() {

    }
}

DomOperator.getConfig = (inConfig, defaultConfig) => {
    let _config = {};

    for (let key in defaultConfig) {
        if (typeof defaultConfig[key] === "object") {
            if (inConfig[key] === undefined) {
                _config[key] = defaultConfig[key];
            } else {
                _config[key] = {};
                for (let childKey in defaultConfig[key]) {
                    _config[key][childKey] = inConfig[key][childKey] ?? defaultConfig[key][childKey];
                }
            }
        } else {
            _config[key] = inConfig[key] ?? defaultConfig[key];
        }
    }

    return _config;
}

});