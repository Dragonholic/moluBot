const SERVER_URL = "http://172.30.1.100:8001";
const MAX_RETRIES = 3;
const RETRY_DELAY = 2000; // 2초
const TIMEOUT = 30000; // 30초

function sleep(ms) {
    java.lang.Thread.sleep(ms);
}

function sendRequest(url, data, method, retries) {
    if (retries === undefined) retries = 0;
    try {
        var connection = org.jsoup.Jsoup.connect(url)
            .ignoreContentType(true)
            .header("Content-Type", "application/json")
            .timeout(TIMEOUT);

        var response;
        if (method === "post") {
            response = connection.requestBody(JSON.stringify(data)).post();
        } else if (method === "get") {
            response = connection.get();
        }
        return JSON.parse(response.body().text());
    } catch (e) {
        Log.e("Error in sendRequest: " + e);
        if (retries < MAX_RETRIES) {
            Log.i("Retrying request... Attempt " + (retries + 1) + " of " + MAX_RETRIES);
            sleep(RETRY_DELAY);
            return sendRequest(url, data, method, retries + 1);
        }
        throw e;
    }
}

function saveMessage(sender, room, message) {
    return sendRequest(SERVER_URL + "/save_message", {
        user_id: sender,
        room: room,
        message: message
    }, "post");
}

function getStats(room) {
    var encodedRoom = encodeURIComponent(room);
    return sendRequest(SERVER_URL + "/chat_stats/" + encodedRoom, null, "get");
}

function processMessage(sender, room, message) {
    return sendRequest(SERVER_URL + "/process_message", {
        user_id: sender,
        room: room,
        message: message
    }, "post");
}

function refreshNews() {
    return sendRequest(SERVER_URL + "/refresh_news", null, "get");
}

function getTodayNews() {
    return sendRequest(SERVER_URL + "/today_news", null, "get");
}

function getMonthlyRankings(room) {
    var encodedRoom = encodeURIComponent(room);
    var response = sendRequest(SERVER_URL + "/monthly_rankings/" + encodedRoom, null, "get");
    return response.rankings;
}

function learnSentence(room, sentence) {
    return sendRequest(SERVER_URL + "/learn_sentence", {
        room: room,
        sentence: sentence
    }, "post");
}

function getLearnedSentence(room) {
    var encodedRoom = encodeURIComponent(room);
    return sendRequest(SERVER_URL + "/get_learned_sentence/" + encodedRoom, null, "get");
}

function recalculateMonthlyRankings(room) {
    var encodedRoom = encodeURIComponent(room);
    return sendRequest(SERVER_URL + "/recalculate_monthly_rankings", { room: encodedRoom }, "post");
}

function getGuide() {
    return "🐾 댕동이 사용 가이드 🐾\n\n" +
           "1️⃣ 댕동이와 대화하기\n" +
           "   사용법: !메시지\n" +
           "   설명: '!'로 시작하는 메시지를 보내면 댕동이가 대답해요.\n\n" +
           "2️⃣ 채팅 통계 확인하기\n" +
           "   명령어: !고인물 또는 !ㄱㅇㅁ\n" +
           "   설명: 이 방의 채팅 통계를 확인할 수 있어요.\n\n" +
           "3️⃣ 성격 분석하기\n" +
           "   명령어: !성격분석 [사용자ID]\n" +
           "   설명: 지정한 사용자의 성격을 분석해요.\n\n" +
           "4️⃣ 출석체크하기\n" +
           "   명령어: ㅊㅊ 또는 !ㅊㅊ\n" +
           "   설명: 오늘의 출석체크를 할 수 있어요.\n\n" +
           "5️⃣ 오늘의 뉴스 보기\n" +
           "   명령어: !뉴스 또는 !ㄴㅅ\n" +
           "   설명: 오늘의 뉴스 요약을 볼 수 있어요.\n\n" +
           "6️⃣ 뉴스 새로고침\n" +
           "   명령어: !뉴스새로고침\n" +
           "   설명: 뉴스를 새로 받아와요. (관리자 전용)\n\n" +
           "7️⃣ 월간 출석 랭킹 확인하기\n" +
           "   명령어: !순위\n" +
           "   설명: 이 방의 월간 출석 랭킹을 확인할 수 있어요.\n\n" +
           "8️⃣ 월간 출석 랭킹 재계산하기\n" +
           "   명령어: !순위업데이트\n" +
           "   설명: 이 방의 월간 출석 랭킹을 재계산해요.\n\n" +
           "9️⃣ 도움말 보기\n" +
           "   명령어: !가이드\n" +
           "   설명: 이 도움말을 다시 볼 수 있어요.\n\n" +
           "즐거운 댕동이와의 대화 되세요! 🐶💖";
}

function crawlLolWorlds() {
    return sendRequest(SERVER_URL + "/crawl_lol_worlds", null, "get");
}

function crawlWorldsTeam() {
    return sendRequest(SERVER_URL + "/crawl_team_worlds", null, "get");
}

function askLolWorldsQuestion(question) {
    try {
        Log.i("LoL Worlds 질문 시도: " + question);
        var response = sendRequest(SERVER_URL + "/lol_worlds_qa", { question: question }, "post");
        Log.d("LoL Worlds 질문 응답: " + JSON.stringify(response));
        return response;
    } catch (e) {
        Log.e("askLolWorldsQuestion 오류: " + e);
        var errorMessage = "알 수 없는 오류가 발생했습니다.";
        if (e.toString().includes("HttpStatusException")) {
            var statusCode = e.toString().match(/status=(\d+)/);
            if (statusCode) {
                errorMessage = "서버 오류 (상태 코드: " + statusCode[1] + ")";
            }
        } else if (e.toString().includes("SocketTimeoutException")) {
            errorMessage = "서버 응답 시간 초과";
        } else if (e.toString().includes("UnknownHostException")) {
            errorMessage = "서버에 연결할 수 없습니다. 네트워크를 확인해주세요.";
        }
        Log.e("askLolWorldsQuestion 상세 오류: " + errorMessage);
        return { status: "error", message: errorMessage };
    }
}

function askWorldsTeamQuestion(question) {
    try {
        Log.i("LoL Worlds 질문 시도: " + question);
        var response = sendRequest(SERVER_URL + "/lol_worlds_team_qa", { question: question }, "post");
        Log.d("LoL Worlds 질문 응답: " + JSON.stringify(response));
        return response;
    } catch (e) {
        Log.e("askWorldsTeamQuestion 오류: " + e);
        var errorMessage = "알 수 없는 오류가 발생했습니다.";
        if (e.toString().includes("HttpStatusException")) {
            var statusCode = e.toString().match(/status=(\d+)/);
            if (statusCode) {
                errorMessage = "서버 오류 (상태 코드: " + statusCode[1] + ")";
            }
        } else if (e.toString().includes("SocketTimeoutException")) {
            errorMessage = "서버 응답 시간 초과";
        } else if (e.toString().includes("UnknownHostException")) {
            errorMessage = "서버에 연결할 수 없습니다. 네트워크를 확인해주세요.";
        }
        Log.e("askWorldsTeamQuestion 상세 오류: " + errorMessage);
        return { status: "error", message: errorMessage };
    }
}


function response(room, msg, sender, isGroupChat, replier, ImageDB, packageName) {
    try {
        saveMessage(sender, room, msg);
        
        if (msg === 'ㅊㅊ' || msg === '!ㅊㅊ') {
            try {
                var response = processMessage(sender, room, "출석체크");
                if (response && response.reply) {
                    replier.reply(response.reply);
                } else {
                    replier.reply("출석체크에 실패했습니다. 나중에 다시 시도해 주세요.");
                }
            } catch (e) {
                Log.e("Error in 출석체크: " + e);
                replier.reply("출석체크 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
            }
            return;
        }
        
        if (msg.charAt(0) === '!') {
            var userMessage = msg.substring(1);
            
            switch (userMessage.split(" ")[0]) {
                case "고인물":
                case "ㄱㅇㅁ":
                    try {
                        var stats = getStats(room);
                        if (stats) {
                            var reply = "🏆 이달의 수다쟁이 명예의 전당 🏆\n\n" +
                                        "🗣️ 수다 폭격기 TOP10:\n" + stats.chat_count.join("\n") + "\n\n" +
                                        "📚 장문의 대가 TOP10:\n" + stats.message_count.join("\n");
                            replier.reply(reply);
                        } else {
                            replier.reply("통계 정보를 가져오는데 실패했습니다. 나중에 다시 시도해 주세요.");
                        }
                    } catch (e) {
                        Log.e("Error in 고인물 stats: " + e);
                        replier.reply("통계 정보를 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
                    }
                    break;

                case "가이드":
                    replier.reply(getGuide());
                    break;

                case "성격분석":
    try {
        var targetUser = userMessage.split(" ")[1];
        if (!targetUser) {
            replier.reply("분석할 사용자를 지정해주세요. 예: !성격분석 사용자이름");
            return;
        }

        var response = processMessage(sender, room, "!성격분석 " + targetUser);
        Log.d("성격분석 서버 응답: " + JSON.stringify(response));

        if (response && response.reply) {
            let analysisResult;
            try {
                analysisResult = typeof response.reply === 'string' ? JSON.parse(response.reply) : response.reply;
            } catch (jsonError) {
                Log.e("성격분석 JSON 파싱 오류: " + jsonError);
                analysisResult = { analysis: response.reply };
            }

            let finalResult = analysisResult.analysis || "분석 결과를 가져오는데 실패했습니다.";

            // 불필요한 문자 제거
            finalResult = finalResult.replace(/^['"]|['"]$/g, '').replace(/\\'/g, "'");
            finalResult = finalResult.replace(/^{?['"]?analysis['"]?:\s*['"]?/, '').replace(/['"]?}?$/, '');

            Log.i("성격분석 최종 결과: " + finalResult);
            replier.reply(finalResult);
        } else {
            Log.w("성격분석 응답 없음 또는 잘못된 형식");
            replier.reply("성격 분석에 실패했습니다. 나중에 다시 시도해 주세요.");
        }
    } catch (e) {
        Log.e("성격분석 처리 중 오류 발생: " + e);
        replier.reply("성격 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
    }
    break;

                case "뉴스":
                case "ㄴㅅ":
                    try {
                        var response = getTodayNews();
                        if (response && response.status === "success") {
                            var summaryText = "🗞️ 오늘의 뉴스 요약 🗞️\n\n";
                            var categories = {
                                "economic": "[경제]",
                                "entertainment": "[연예]",
                                "sports": "[스포츠]"
                            };
                            for (var category in response.news_summary) {
                                summaryText += categories[category] + "\n" + response.news_summary[category] + "\n\n";
                            }
                            replier.reply(summaryText);
                        } else {
                            replier.reply("오늘의 뉴스를 가져오는데 실패했습니다. 나중에 다시 시도해 주세요.");
                        }
                    } catch (e) {
                        Log.e("Error in 오늘뉴스: " + e);
                        replier.reply("뉴스를 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
                    }
                    break;

                case "뉴스새로고침":
                    if (sender === "짬뽕순두부" || sender === "채채") {
                        try {
                            var response = refreshNews();
                            if (response && response.status === "success") {
                                replier.reply("뉴스가 성공적으로 새로고침되었습니다.");
                            } else {
                                replier.reply("뉴스 새로고침 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
                            }
                        } catch (e) {
                            Log.e("Error in 뉴스새로고침: " + e);
                        }
                    } else {
                        replier.reply("이 명령어는 관리자만 사용할 수 있습니다.");
                    }
                    break;

                case "순위":
                    try {
                        var rankings = getMonthlyRankings(room);
                        if (rankings) {
                            replier.reply(rankings);
                        } else {
                            replier.reply("월간 랭킹을 가져오는데 실패했습니다. 나중에 다시 시도해 주세요.");
                        }
                    } catch (e) {
                        Log.e("Error in 월간랭킹: " + e);
                        replier.reply("월간 랭킹을 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
                    }
                    break;

                case "학습":
                    var sentence = userMessage.substring(3).trim();
                    try {
                        var response = learnSentence(room, sentence);
                        if (response && response.status === "success") {
                            replier.reply("새로운 문장을 학습했어요: " + sentence);
                        } else {
                            replier.reply("문장 학습에 실패했습니다. 나중에 다시 시도해 주세요.");
                        }
                    } catch (e) {
                        Log.e("Error in 학습: " + e);
                        replier.reply("문장 학습 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
                    }
                    break;

                case "학습확인":
                    try {
                        var response = getLearnedSentence(room);
                        if (response && response.sentence) {
                            replier.reply("현재 학습된 문장: " + response.sentence);
                        } else {
                            replier.reply("현재 학습된 문장이 없습니다.");
                        }
                    } catch (e) {
                        Log.e("Error in 학습확인: " + e);
                        replier.reply("학습된 문장을 확인하는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
                    }
                    break;

                default:
                    try {
                        var response = processMessage(sender, room, userMessage);
                        
                        if (response && response.reply) {
                            replier.reply(response.reply);
                        } else {
                            replier.reply("지금은 대답하기 어렵습니다. 나중에 다시 말걸어 주세요.");
                        }
                    } catch (e) {
                        Log.e("Error in general message processing: " + e);
                        replier.reply("메시지 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
                    }
            }
        }
    } catch (e) {
        Log.e("Error in response function: " + e);
        replier.reply("오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
    }
}