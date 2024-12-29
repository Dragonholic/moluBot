const SERVER_URL = ""; // 서버의 기본 URL 설정
const TIMEOUT = 30000; // 요청 타임아웃 시간 (ms)

/**
 * HTTP 요청을 보내는 기본 함수
 * @param {string} endpoint - API 엔드포인트
 * @param {object} data - POST 요청시 전송할 데이터
 * @param {string} method - HTTP 메서드 (get/post)
 */
function sendRequest(endpoint, data = null, method = "get") {
    try {
        var connection = org.jsoup.Jsoup.connect(SERVER_URL + endpoint)
            .ignoreContentType(true)
            .header("Content-Type", "application/json")
            .timeout(TIMEOUT);

        var response;
        if (method === "post") {
            response = connection.requestBody(JSON.stringify(data)).post();
        } else {
            response = connection.get();
        }
        
        return JSON.parse(response.body().text());
    } catch (e) {
        Log.e("Error in sendRequest: " + e);
        throw e;
    }
}

/**
 * 메시지를 서버로 전송
 */
function sendMessage(sender, room, message) {
    return sendRequest("/messages", {
        user_id: sender,
        room: room,
        message: message
    }, "post");
}

/**
 * 채팅방 통계 조회
 */
function getStats(room) {
    return sendRequest("/chat_stats/" + encodeURIComponent(room));
}

/**
 * 알림 테스트
 */
function testNotification(type) {
    return sendRequest("/test_notification/" + type, null, "post");
}
