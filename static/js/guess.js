(function () {
    "use strict";

    const API = "/api";

    const $setup = document.getElementById("guess-setup");
    const $play = document.getElementById("guess-play");
    const $result = document.getElementById("guess-result");
    const $difficulty = document.getElementById("difficulty");
    const $btnStart = document.getElementById("btn-start");
    const $hintLabel = document.getElementById("hint-label");
    const $hintValue = document.getElementById("hint-value");
    const $guessesNum = document.getElementById("guesses-num");
    const $guessInput = document.getElementById("guess-input");
    const $btnGuess = document.getElementById("btn-guess");
    const $btnGiveup = document.getElementById("btn-giveup");
    const $comparisonHistory = document.getElementById("comparison-history");
    const $resultMessage = document.getElementById("result-message");
    const $answerCard = document.getElementById("answer-card");
    const $btnAgain = document.getElementById("btn-again");
    const $toast = document.getElementById("guess-toast");
    const $toastMsg = document.getElementById("guess-toast-msg");
    const $toastRetry = document.getElementById("guess-toast-retry");

    var lastRetryFn = null;

    function showToast(msg, retryFn) {
        if ($toast && $toastMsg) {
            $toastMsg.textContent = msg || "请求失败";
            $toast.style.display = "flex";
        }
        lastRetryFn = typeof retryFn === "function" ? retryFn : null;
    }

    function hideToast() {
        if ($toast) $toast.style.display = "none";
        lastRetryFn = null;
    }

    function resultSymbol(res) {
        if (res === "high") return "↑";
        if (res === "low") return "↓";
        if (res === "correct") return "√";
        if (res === "early") return "↑";
        if (res === "late") return "↓";
        return "";
    }

    function resultClass(res) {
        if (res === "high" || res === "early") return "result-arrow-up";
        if (res === "low" || res === "late") return "result-arrow-down";
        if (res === "correct") return "result-correct";
        return "";
    }

    function showScreen(which) {
        $setup.style.display = which === "setup" ? "block" : "none";
        $play.style.display = which === "play" ? "block" : "none";
        $result.style.display = which === "result" ? "block" : "none";
    }

    function startGame() {
        const difficulty = parseInt($difficulty.value, 10);
        hideToast();
        if ($btnStart) { $btnStart.disabled = true; $btnStart.textContent = "加载中..."; }
        fetch(API + "/guess/start?difficulty=" + difficulty)
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (res.error) {
                    showToast(res.error, startGame);
                    return;
                }
                $hintLabel.textContent = res.hint.label;
                $hintValue.textContent = res.hint.value != null && res.hint.value !== "" ? Number(res.hint.value).toFixed(1) : "—";
                $guessesNum.textContent = res.total_guesses;
                $guessesNum.setAttribute("data-total", String(res.total_guesses));
                $comparisonHistory.innerHTML = "";
                $guessInput.value = "";
                $guessInput.focus();
                showScreen("play");
            })
            .catch(function () { showToast("请求失败", startGame); })
            .finally(function () {
                if ($btnStart) { $btnStart.disabled = false; $btnStart.textContent = "开始游戏"; }
            });
    }

    function fmtVal(v) {
        return v != null && v !== "" ? (typeof v === "number" ? (v === Math.round(v) ? String(v) : v.toFixed(1)) : String(v)) : "—";
    }

    function renderAnswerCard(emp) {
        const labels = {
            overall_rank: "排名", era: "时代", temple_posthumous_title: "庙/谥/称号", name: "姓名", short_comment: "短评",
            virtue: "德", wisdom: "智", fitness: "体", beauty: "美", diligence: "劳", ambition: "雄心", dignity: "尊严",
            magnanimity: "气量", desire_self_control: "欲望自控", personnel_management: "人事管理", national_power: "国力",
            military_diplomacy: "军事外交", public_support: "民心", economy_livelihood: "经济民生", historical_impact: "历史影响",
            overall_score: "综合评分"
        };
        const keys = ["overall_rank", "era", "temple_posthumous_title", "name", "short_comment",
            "virtue", "wisdom", "fitness", "beauty", "diligence", "ambition", "dignity", "magnanimity",
            "desire_self_control", "personnel_management", "national_power", "military_diplomacy",
            "public_support", "economy_livelihood", "historical_impact", "overall_score"];
        let html = "<dl>";
        keys.forEach(function (key) {
            const label = labels[key] || key;
            const display = fmtVal(emp[key]);
            html += "<dt>" + label + "</dt><dd>" + display + "</dd>";
        });
        html += "</dl>";
        return html;
    }

    function submitGuess() {
        const guess = $guessInput.value.trim();
        if (!guess) {
            $guessInput.focus();
            return;
        }
        var btn = $btnGuess;
        btn.disabled = true;
        fetch(API + "/guess/guess", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ guess: guess })
        })
            .then(function (r) {
                return r.json().then(function (res) {
                    if (!r.ok && res && res.error) {
                        var err = new Error(res.error);
                        err.response = res;
                        throw err;
                    }
                    return res;
                });
            })
            .then(function (res) {
                btn.disabled = false;
                if (res.error) {
                    showToast(res.error, submitGuess);
                    return;
                }
                if (!res.comparison || !Array.isArray(res.comparison)) {
                    showToast("返回数据异常，请重试", submitGuess);
                    return;
                }
                hideToast();
                $guessesNum.textContent = res.guesses_left;
                var round = document.createElement("div");
                round.className = "guess-round";
                round.innerHTML = "<div class=\"guess-round-title\">猜的是：<strong>" + (res.guess_name || guess) + "</strong>（排名 " + (res.guess_rank != null ? res.guess_rank : "—") + "）</div>";
                var table = "<table class=\"guess-round-table\"><thead><tr><th>维度</th><th>猜的数值</th><th>对比</th></tr></thead><tbody>";
                res.comparison.forEach(function (item) {
                    var val = item.value != null && item.value !== "" ? (typeof item.value === "number" ? (item.value === Math.round(item.value) ? String(item.value) : Number(item.value).toFixed(1)) : String(item.value)) : "—";
                    var sym = resultSymbol(item.result);
                    table += "<tr><th>" + item.label + "</th><td class=\"guess-val\">" + val + "</td><td class=\"" + resultClass(item.result) + "\">" + sym + "</td></tr>";
                });
                table += "</tbody></table>";
                round.innerHTML += table;
                $comparisonHistory.appendChild(round);
                $guessInput.value = "";
                $guessInput.focus();

                if (res.won) {
                    $resultMessage.textContent = "恭喜，猜中了！";
                    $resultMessage.className = "result-message won";
                    $answerCard.innerHTML = "<p><strong>答案皇帝</strong></p>" + renderAnswerCard(res.answer);
                    showScreen("result");
                    return;
                }
                if (res.guesses_left <= 0) {
                    $resultMessage.textContent = "次数用完了，答案是：";
                    $resultMessage.className = "result-message lost";
                    $answerCard.innerHTML = renderAnswerCard(res.answer);
                    showScreen("result");
                    return;
                }
            })
            .catch(function (e) {
                btn.disabled = false;
                showToast(e.message || "请求失败", submitGuess);
            });
    }

    function giveUp() {
        hideToast();
        fetch(API + "/guess/giveup", { method: "POST" })
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (res.error) {
                    showToast(res.error, giveUp);
                    return;
                }
                if (res.answer) {
                    $resultMessage.textContent = "已放弃，答案是：";
                    $resultMessage.className = "result-message lost";
                    $answerCard.innerHTML = renderAnswerCard(res.answer);
                    showScreen("result");
                }
            })
            .catch(function () { showToast("请求失败", giveUp); });
    }

    $btnStart.addEventListener("click", startGame);
    $btnGuess.addEventListener("click", submitGuess);
    $btnGiveup.addEventListener("click", giveUp);
    $guessInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") submitGuess();
    });
    $btnAgain.addEventListener("click", function () {
        $guessInput.value = "";
        hideToast();
        showScreen("setup");
    });

    if ($toastRetry) {
        $toastRetry.addEventListener("click", function () {
            hideToast();
            if (lastRetryFn) lastRetryFn();
        });
    }
})();
