const SERVER_URL = "";

function response(room, msg, sender, isGroupChat, replier) {
    try {
        // 모든 메시지를 서버로 전송
        let result = sendToServer({
            message: msg,
            room: room,
            sender: sender,
            isGroupChat: isGroupChat
        });
        
        // 서버 응답 로깅
        Log.i("서버 응답: " + JSON.stringify(result));
        
    } catch (e) {
        Log.e("오류 발생: " + e);
        replier.reply("오류 발생: " + e);
    }
}

function sendToServer(data) {
    try {
        var response = org.jsoup.Jsoup.connect(SERVER_URL + "/message")
            .ignoreContentType(true)
            .header("Content-Type", "application/json")
            .requestBody(JSON.stringify(data))
            .timeout(5000)
            .post();
            
        return JSON.parse(response.body().text());
    } catch (e) {
        Log.e("서버 전송 오류: " + e);
        return { "response": "연결 실패: " + e.message };
    }
} 