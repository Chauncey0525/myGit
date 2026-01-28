(function () {
    "use strict";

    const API = "/api";
    const LS_KEY = "emperor_diy_ranking";
    const LS_KEY_SAVED = "emperor_diy_saved";

    const $eraList = document.getElementById("era-list");
    const $rankList = document.getElementById("rank-list");
    const $rankDrop = document.getElementById("rank-drop");
    const $diySearch = document.getElementById("diy-search");
    const $diyReset = document.getElementById("diy-reset");
    const $diySave = document.getElementById("diy-save");
    const $diySavedSelect = document.getElementById("diy-saved-select");
    const $diyLoad = document.getElementById("diy-load");
    const $diyDelete = document.getElementById("diy-delete");
    const $diyLeftSort = document.getElementById("diy-left-sort");

    const LS_KEY_LEFT_SORT = "emperor_diy_left_sort";

    /** 朝代顺序（历史先后），未出现的朝代排在后面 */
    const ERA_ORDER = ["秦", "西汉", "新", "东汉", "成汉", "曹魏", "蜀汉", "孙吴", "西晋", "前赵", "前燕", "前凉", "东晋", "后赵", "前秦", "冉魏", "前蜀", "后燕", "南燕", "西秦", "后秦", "后凉", "南凉", "北凉", "西凉", "北燕", "胡夏", "北魏", "南朝宋", "南齐", "南梁", "陈", "西魏", "东魏", "北齐", "北周", "隋", "唐", "武周", "吴越", "闽国", "南吴", "南楚", "前蜀", "后梁", "辽", "后唐", "南汉", "南平", "后蜀", "后晋", "南唐", "后汉", "后周", "北汉", "北宋", "西夏", "西辽", "金", "南宋", "蒙古", "元", "明", "清", "未分类"];

    let allEmperors = [];
    let myRanking = [];
    let leftSortMode = "era";

    function loadAll() {
        fetch(API + "/emperors/all")
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (res.error) {
                    $eraList.innerHTML = "<p class=\"error-msg\">" + res.error + "</p>";
                    return;
                }
                allEmperors = res.data || [];
                renderLeftList();
            })
            .catch(function () {
                $eraList.innerHTML = "<p class=\"error-msg\">加载失败</p>";
            });
    }

    function matchSearch(emp, q) {
        if (!q) return true;
        const s = (emp.name || "") + " " + (emp.temple_posthumous_title || "");
        return s.indexOf(q) !== -1;
    }

    function rankKey(emp) {
        return emp && emp.overall_rank != null ? String(emp.overall_rank) : "";
    }

    function appendEmperorLi(ul, emp) {
        const li = document.createElement("li");
        li.className = "emperor-item";
        li.draggable = true;
        li.dataset.rank = String(emp.overall_rank);
        li.textContent = displayName(emp);
        li.title = displayName(emp);
        li._emp = emp;
        li.addEventListener("dragstart", onLeftDragStart);
        li.addEventListener("dragend", function () { li.classList.remove("dragging"); });
        li.addEventListener("dblclick", onLeftDblClick);
        ul.appendChild(li);
    }

    function renderLeftList() {
        const q = ($diySearch && $diySearch.value) ? $diySearch.value.trim() : "";
        const selected = new Set(myRanking.map(function (x) { return rankKey(x); }));
        const filtered = allEmperors.filter(function (emp) {
            return !selected.has(rankKey(emp)) && matchSearch(emp, q);
        });

        $eraList.innerHTML = "";

        if (leftSortMode === "rank") {
            filtered.sort(function (a, b) {
                const ra = a.overall_rank != null ? a.overall_rank : 999999;
                const rb = b.overall_rank != null ? b.overall_rank : 999999;
                return ra - rb;
            });
            const ul = document.createElement("ul");
            ul.className = "emperor-list";
            filtered.forEach(function (emp) { appendEmperorLi(ul, emp); });
            $eraList.appendChild(ul);
        } else {
            const byEra = {};
            filtered.forEach(function (emp) {
                const era = emp.era || "未分类";
                if (!byEra[era]) byEra[era] = [];
                byEra[era].push(emp);
            });
            const eras = Object.keys(byEra);
            eras.sort(function (a, b) {
                const ia = ERA_ORDER.indexOf(a);
                const ib = ERA_ORDER.indexOf(b);
                if (ia !== -1 && ib !== -1) return ia - ib;
                if (ia !== -1) return -1;
                if (ib !== -1) return 1;
                return a.localeCompare(b);
            });
            eras.forEach(function (era) {
                const section = document.createElement("section");
                section.className = "era-section";
                section.innerHTML = "<h3 class=\"era-title\">" + escapeHtml(era) + "</h3>";
                const ul = document.createElement("ul");
                ul.className = "emperor-list";
                byEra[era].forEach(function (emp) { appendEmperorLi(ul, emp); });
                section.appendChild(ul);
                $eraList.appendChild(section);
            });
        }
    }

    function escapeHtml(s) {
        if (!s) return "";
        const div = document.createElement("div");
        div.textContent = s;
        return div.innerHTML;
    }

    function displayName(emp) {
        const dashOnly = /^[\s\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFE63\uFF0D\-]+$/;
        const dashPrefix = /^[\s\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFE63\uFF0D\-]+/;

        let title = (emp && emp.temple_posthumous_title) ? String(emp.temple_posthumous_title).trim() : "";
        if (title && dashOnly.test(title)) title = "";

        let name = (emp && emp.name) ? String(emp.name).trim() : "";
        if (name) name = name.replace(dashPrefix, "").trim() || name;
        if (title && name) return title + "——" + name;
        return name || title || "-";
    }

    function onLeftDragStart(e) {
        const emp = e.currentTarget && e.currentTarget._emp;
        if (!emp) return;
        e.dataTransfer.effectAllowed = "copy";
        e.dataTransfer.setData("application/json", JSON.stringify(emp));
        e.dataTransfer.setData("text/plain", String(emp.overall_rank));
        e.currentTarget.classList.add("dragging");
    }

    /** 左侧双击：将该帝王追加到右侧排行榜末尾（最低排行） */
    function onLeftDblClick(e) {
        const li = e.target.closest(".emperor-item");
        const emp = li && li._emp;
        if (!emp) return;
        const exists = myRanking.some(function (x) { return rankKey(x) === rankKey(emp); });
        if (!exists) {
            myRanking.push(emp);
            saveRanking();
            renderRanking();
            renderLeftList();
        }
    }

    function loadRanking() {
        try {
            const raw = localStorage.getItem(LS_KEY);
            myRanking = raw ? JSON.parse(raw) : [];
            if (!Array.isArray(myRanking)) myRanking = [];
        } catch (err) {
            myRanking = [];
        }
        renderRanking();
        renderLeftList();
    }

    function saveRanking() {
        try {
            localStorage.setItem(LS_KEY, JSON.stringify(myRanking));
        } catch (err) {}
    }

    function removeRankingAt(index) {
        if (!Number.isFinite(index)) return null;
        if (index < 0 || index >= myRanking.length) return null;
        const removed = myRanking.splice(index, 1)[0] || null;
        saveRanking();
        renderRanking();
        renderLeftList();
        return removed;
    }

    function getSavedStore() {
        try {
            const raw = localStorage.getItem(LS_KEY_SAVED);
            const obj = raw ? JSON.parse(raw) : {};
            return obj && typeof obj === "object" ? obj : {};
        } catch (err) {
            return {};
        }
    }

    function setSavedStore(obj) {
        try {
            localStorage.setItem(LS_KEY_SAVED, JSON.stringify(obj));
        } catch (err) {}
    }

    function refreshSavedSelect() {
        const store = getSavedStore();
        const names = Object.keys(store).sort();
        $diySavedSelect.innerHTML = "<option value=\"\">请选择</option>";
        names.forEach(function (n) {
            const opt = document.createElement("option");
            opt.value = n;
            opt.textContent = n;
            $diySavedSelect.appendChild(opt);
        });
    }

    function resetRanking() {
        if (!confirm("确定要清空当前排行榜吗？")) return;
        myRanking = [];
        saveRanking();
        renderRanking();
        renderLeftList();
    }

    function saveNamed() {
        const name = prompt("请输入排行榜名称：");
        if (name == null) return;
        const trimmed = (name || "").trim();
        if (!trimmed) {
            alert("名称不能为空");
            return;
        }
        const store = getSavedStore();
        if (store[trimmed] && !confirm("已存在同名排行榜，是否覆盖？")) return;
        store[trimmed] = myRanking.slice();
        setSavedStore(store);
        refreshSavedSelect();
        alert("已保存为：「" + trimmed + "」");
    }

    function loadNamed() {
        const name = ($diySavedSelect && $diySavedSelect.value) ? $diySavedSelect.value.trim() : "";
        if (!name) {
            alert("请先选择一个已保存的排行榜");
            return;
        }
        const store = getSavedStore();
        const list = store[name];
        if (!list || !Array.isArray(list)) {
            alert("未找到该排行榜");
            return;
        }
        myRanking = list.slice();
        saveRanking();
        renderRanking();
        renderLeftList();
    }

    function deleteNamed() {
        const name = ($diySavedSelect && $diySavedSelect.value) ? $diySavedSelect.value.trim() : "";
        if (!name) {
            alert("请先选择要删除的排行榜");
            return;
        }
        if (!confirm("确定要删除「" + name + "」吗？")) return;
        const store = getSavedStore();
        delete store[name];
        setSavedStore(store);
        refreshSavedSelect();
    }

    function renderRanking() {
        $rankList.innerHTML = "";
        myRanking.forEach(function (emp, index) {
            const li = document.createElement("li");
            li.className = "rank-item";
            li.draggable = true;
            li.dataset.index = String(index);
            li.dataset.rank = String(emp.overall_rank);
            li.innerHTML = "<span class=\"rank-num\">" + (index + 1) + "</span><span class=\"rank-name\">" + escapeHtml(displayName(emp)) + "</span>";
            li._emp = emp;
            li._index = index;
            li.addEventListener("dragstart", onRightDragStart);
            li.addEventListener("dragover", onRightDragOver);
            li.addEventListener("dragleave", function (e) {
                if (!e.currentTarget.contains(e.relatedTarget)) e.currentTarget.classList.remove("drag-over");
            });
            li.addEventListener("dblclick", onRightDblClick);
            li.addEventListener("drop", onRightDrop);
            li.addEventListener("dragend", onRightDragEnd);
            $rankList.appendChild(li);
        });
    }

    function onRightDragStart(e) {
        const index = parseInt(e.currentTarget.dataset.index, 10);
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", "index:" + index);
        e.currentTarget.classList.add("dragging");
    }

    function onRightDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = "move";
        if ($rankDrop) $rankDrop.classList.remove("drag-over");
        const tr = e.target.closest(".rank-item");
        if (tr) {
            $rankList.querySelectorAll(".rank-item.drag-over").forEach(function (el) { if (el !== tr) el.classList.remove("drag-over"); });
            tr.classList.add("drag-over");
        }
    }

    function onRightDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        document.querySelectorAll(".rank-item.drag-over").forEach(function (el) { el.classList.remove("drag-over"); });
        const json = e.dataTransfer.getData("application/json");
        const text = e.dataTransfer.getData("text/plain");
        const dropLi = e.target.closest(".rank-item");
        const dropIndex = dropLi ? parseInt(dropLi.dataset.index, 10) : myRanking.length;

        if (json) {
            try {
                const emp = JSON.parse(json);
                if (emp && emp.overall_rank != null) {
                    const exists = myRanking.some(function (x) { return rankKey(x) === rankKey(emp); });
                    if (!exists) {
                        myRanking.splice(dropIndex, 0, emp);
                        saveRanking();
                        renderRanking();
                        renderLeftList();
                    }
                }
            } catch (err) {}
        } else if (text.indexOf("index:") === 0) {
            const fromIndex = parseInt(text.slice(6), 10);
            if (!Number.isFinite(fromIndex)) return;
            if (fromIndex === dropIndex) return;
            const item = myRanking.splice(fromIndex, 1)[0];
            if (item) {
                const insertIndex = fromIndex < dropIndex ? Math.max(0, dropIndex - 1) : dropIndex;
                myRanking.splice(insertIndex, 0, item);
                saveRanking();
                renderRanking();
            }
        }
    }

    /** 右侧双击：移出排行榜（回到左侧名单） */
    function onRightDblClick(e) {
        const idx = parseInt(e.currentTarget.dataset.index, 10);
        removeRankingAt(idx);
    }

    function onRightDragEnd(e) {
        e.currentTarget.classList.remove("dragging");
        document.querySelectorAll(".rank-item.drag-over").forEach(function (el) { el.classList.remove("drag-over"); });
    }

    $rankDrop.addEventListener("dragover", function (e) {
        // 在具体行上方拖拽时，由行本身处理（避免父容器抢占导致排序失效）
        if (e.target.closest && e.target.closest(".rank-item")) return;
        e.preventDefault();
        const types = e.dataTransfer && e.dataTransfer.types ? Array.from(e.dataTransfer.types) : [];
        e.dataTransfer.dropEffect = types.indexOf("application/json") !== -1 ? "copy" : "move";
        $rankDrop.classList.add("drag-over");
    });
    $rankDrop.addEventListener("dragleave", function (e) {
        if (!$rankDrop.contains(e.relatedTarget)) $rankDrop.classList.remove("drag-over");
    });
    $rankDrop.addEventListener("drop", function (e) {
        // 如果落点在具体行上，交给行本身 drop 处理
        if (e.target.closest && e.target.closest(".rank-item")) return;
        e.preventDefault();
        $rankDrop.classList.remove("drag-over");
        const json = e.dataTransfer.getData("application/json");
        const text = e.dataTransfer.getData("text/plain");
        if (json) {
            try {
                const emp = JSON.parse(json);
                if (emp && emp.overall_rank != null) {
                    const exists = myRanking.some(function (x) { return rankKey(x) === rankKey(emp); });
                    if (!exists) {
                        myRanking.push(emp);
                        saveRanking();
                        renderRanking();
                        renderLeftList();
                    }
                }
            } catch (err) {}
            return;
        }

        // 右侧空白处 drop：允许把右侧拖动项放到末尾
        if (text && text.indexOf("index:") === 0) {
            const fromIndex = parseInt(text.slice(6), 10);
            if (!Number.isFinite(fromIndex)) return;
            const item = myRanking.splice(fromIndex, 1)[0];
            if (item) {
                myRanking.push(item);
                saveRanking();
                renderRanking();
            }
        }
    });

    // 右侧拖回左侧：拖到左侧名单区域会从排行榜移除
    if ($eraList) {
        $eraList.addEventListener("dragover", function (e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = "move";
            $eraList.classList.add("drag-over");
        });
        $eraList.addEventListener("dragleave", function (e) {
            if (!$eraList.contains(e.relatedTarget)) $eraList.classList.remove("drag-over");
        });
        $eraList.addEventListener("drop", function (e) {
            e.preventDefault();
            $eraList.classList.remove("drag-over");
            const text = e.dataTransfer.getData("text/plain") || "";
            if (text.indexOf("index:") === 0) {
                const fromIndex = parseInt(text.slice(6), 10);
                if (Number.isFinite(fromIndex)) removeRankingAt(fromIndex);
            }
        });
    }

    if ($diySearch) $diySearch.addEventListener("input", renderLeftList);
    if ($diyReset) $diyReset.addEventListener("click", resetRanking);
    if ($diySave) $diySave.addEventListener("click", saveNamed);
    if ($diyLoad) $diyLoad.addEventListener("click", loadNamed);
    if ($diyDelete) $diyDelete.addEventListener("click", deleteNamed);

    try {
        const saved = localStorage.getItem(LS_KEY_LEFT_SORT);
        if (saved === "era" || saved === "rank") {
            leftSortMode = saved;
            if ($diyLeftSort) $diyLeftSort.value = saved;
        }
    } catch (err) {}
    if ($diyLeftSort) {
        $diyLeftSort.addEventListener("change", function () {
            leftSortMode = $diyLeftSort.value === "rank" ? "rank" : "era";
            try { localStorage.setItem(LS_KEY_LEFT_SORT, leftSortMode); } catch (err) {}
            renderLeftList();
        });
    }

    loadAll();
    loadRanking();
    refreshSavedSelect();
})();
