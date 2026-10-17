// Keep certificate verification enabled; use the official Gitee mirror if the
// legacy official download server is unavailable (including expired TLS).
const yuxuanCloudDownload = CloudDownload.download;
function yuxuanOfficialMirror(url) {
    if (typeof url !== 'string') return null;
    const path = url.match(/^https?:\/\/download\.mixlylibs\.cloud\/mixly-packages\/(.+)$/);
    const legacy = url.match(/^https?:\/\/mixlylibs\.cloud:8099\/mixly2\/cloud-libraries\/raw\/(?:master|develop)\/(.+)$/);
    const relative = path ? path[1] : legacy ? legacy[1] : null;
    return relative ? 'https://gitee.com/mixly2/cloud-libraries/raw/master/' + relative : null;
}
CloudDownload.download = async (url, directory, options = {}) => {
    const mirror = yuxuanOfficialMirror(url);
    if (/^http:\/\/mixlylibs\.cloud:8099\//i.test(url) && mirror)
        return yuxuanCloudDownload(mirror, directory, options);
    const result = await yuxuanCloudDownload(url, directory, mirror ? {...options, error: null, timeout: null} : options);
    if (result[0] && mirror) return yuxuanCloudDownload(mirror, directory, options);
    return result;
};
