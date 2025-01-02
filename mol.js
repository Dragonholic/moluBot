const SERVER_URL = ""; // 라즈베리파이 서버 주소
const TIMEOUT = 30000;

function response(room, msg, sender, isGroupChat, replier, imageDB, packageName) {
    try {
        // UI 스레드 문제 해결을 위해 Thread 사용
        new java.lang.Thread({
            run() {
                try {
                    // 명령어로 시작하는 메시지만 처리
                    if (msg.startsWith('*')) {
                        let result = sendMessage(sender, room, msg);
                        if (result && result.response) {
                            replier.reply(result.response);
                        }
                    }
                } catch (e) {
                    Log.e("Thread Error: " + e);
                    replier.reply("오류가 발생했습니다: " + e.message);
                }
            }
        }).start();
    } catch (e) {
        Log.e("Error in response: " + e);
        replier.reply("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
    }
}

function sendRequest(endpoint, data, method) {
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
            Log.i("서버 응답: " + response.body().text());  // 응답 로깅 추가
            return JSON.parse(response.body().text());
        } catch (e) {
            Log.e("Request failed: " + e);
            if (e.toString().includes("timeout")) {
                return { "response": "서버 응답 시간이 초과되었습니다." };
            }
            return { "response": "서버 연결 오류: " + e.message };
        }
    } catch (e) {
        Log.e("Error in sendRequest: " + e);
        return { "response": "요청 처리 중 오류가 발생했습니다." };
    }
}

function sendMessage(sender, room, message) {
    return sendRequest("/messages", {
        user_id: sender,
        room: room,
        message: message
    }, "post");
}

function getStats(room) {
    return sendRequest("/chat_stats/" + encodeURIComponent(room), null, "get");
}

