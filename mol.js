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
        try {
            if (method === "post") {
                response = connection.requestBody(JSON.stringify(data)).post();
            } else {
                response = connection.get();
            }
        } catch (e) {
            if (e.toString().includes("timeout")) {
                return { "response": "서버가 응답하지 않습니다. 잠시 후 다시 시도해주세요." };
            }
            throw e;
        }
        
        return JSON.parse(response.body().text());
    } catch (e) {
        Log.e("Error in sendRequest: " + e);
        return { "response": "서버가 응답하지 않습니다. 잠시 후 다시 시도해주세요." };
    }
}

/**
 * 메시지를 서버로 전송
 * @param {string} sender - 메시지를 보낸 사용자의 ID
 * @param {string} room - 메시지가 전송된 채팅방 이름
 * @param {string} message - 전송할 메시지 내용
 * @returns {object} 서버 응답 데이터
 * 
 * 예시:
 * sendMessage("user123", "블루아카이브방", "안녕하세요")
 * - user123이라는 사용자가
 * - "블루아카이브방"이라는 채팅방에서
 * - "안녕하세요"라는 메시지를 전송
 */
function sendMessage(sender, room, message) {
    return sendRequest("/messages", {
        user_id: sender,  // 메시지 발신자 ID
        room: room,       // 채팅방 이름
        message: message  // 메시지 내용
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
