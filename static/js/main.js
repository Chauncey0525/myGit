(function () {
    "use strict";

    const API = "/api";
    const ERA_ORDER = ["秦", "西汉", "新", "东汉", "成汉", "曹魏", "蜀汉", "孙吴", "西晋", "前赵", "前燕", "前凉", "东晋", "后赵", "前秦", "冉魏", "前蜀", "后燕", "南燕", "西秦", "后秦", "后凉", "南凉", "北凉", "西凉", "北燕", "胡夏", "北魏", "南朝宋", "南齐", "南梁", "陈", "西魏", "东魏", "北齐", "北周", "隋", "唐", "武周", "吴越", "闽国", "南吴", "南楚", "前蜀", "后梁", "辽", "后唐", "南汉", "南平", "后蜀", "后晋", "南唐", "后汉", "后周", "北汉", "北宋", "西夏", "西辽", "金", "南宋", "蒙古", "元", "明", "清"];

    let currentPage = 1;
    let total = 0;
    let perPage = 50;
    let allEmperors = [];

    const SCORE_KEYS = ["virtue", "wisdom", "fitness", "beauty", "diligence", "ambition", "dignity", "magnanimity", "desire_self_control", "personnel_management", "national_power", "military_diplomacy", "public_support", "economy_livelihood", "historical_impact"];
    const COLSPAN = 4 + SCORE_KEYS.length + 1;

    const $tbody = document.getElementById("tbody");
    const $pagination = document.getElementById("pagination");
    const $search = document.getElementById("search");
    const $era = document.getElementById("era");
    const $perPage = document.getElementById("per_page");
    let sortField = "overall_rank";
    let sortOrder = "asc";
    const $detailModal = document.getElementById("detail-modal");
    const $detailBody = document.getElementById("detail-body");
    const $modalClose = document.getElementById("modal-close");
    const $modalBackdrop = document.getElementById("modal-backdrop");

    function getQuery() {
        const params = new URLSearchParams();
        params.set("page", String(currentPage));
        params.set("per_page", String(perPage));
        params.set("sort", sortField);
        params.set("order", sortOrder);
        const era = $era.value.trim();
        if (era) params.set("era", era);
        const search = $search.value.trim();
        if (search) params.set("search", search);
        return params.toString();
    }

    function loadEras() {
        fetch(API + "/eras")
            .then(function (r) { return r.json(); })
            .then(function (res) {
                const list = res.data || [];
                list.sort(function (a, b) {
                    const ia = ERA_ORDER.indexOf(a);
                    const ib = ERA_ORDER.indexOf(b);
                    if (ia !== -1 && ib !== -1) return ia - ib;
                    if (ia !== -1) return -1;
                    if (ib !== -1) return 1;
                    return (a || "").localeCompare(b || "");
                });
                $era.innerHTML = "<option value=\"\">全部</option>";
                list.forEach(function (e) {
                    const opt = document.createElement("option");
                    opt.value = e;
                    opt.textContent = e;
                    $era.appendChild(opt);
                });
            })
            .catch(function () {});
    }

    function loadEmperors() {
        const q = getQuery();
        fetch(API + "/emperors?" + q)
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (res.error) {
                    $tbody.innerHTML = "<tr><td colspan=\"" + COLSPAN + "\">" + res.error + "</td></tr>";
                    return;
                }
                allEmperors = res.data || [];
                total = res.total || 0;
                renderTable(allEmperors);
                renderPagination();
            })
            .catch(function (err) {
                $tbody.innerHTML = "<tr><td colspan=\"" + COLSPAN + "\">加载失败</td></tr>";
            });
    }

    function fmtScore(v) {
        return v != null && v !== "" ? Number(v).toFixed(1) : "-";
    }

    function renderTable(rows) {
        $tbody.innerHTML = "";
        rows.forEach(function (emp) {
            const tr = document.createElement("tr");
            tr.dataset.rank = String(emp.overall_rank);
            let cells = "<td class=\"col-rank\">" + (emp.overall_rank != null ? emp.overall_rank : "-") + "</td>" +
                "<td class=\"col-era\">" + (emp.era || "-") + "</td>" +
                "<td class=\"col-title\">" + (emp.temple_posthumous_title || "-") + "</td>" +
                "<td class=\"col-name\">" + (emp.name || "-") + "</td>";
            SCORE_KEYS.forEach(function (k) { cells += "<td class=\"col-num\">" + fmtScore(emp[k]) + "</td>"; });
            cells += "<td class=\"col-score\">" + fmtScore(emp.overall_score) + "</td>";
            tr.innerHTML = cells;
            tr.addEventListener("click", function () { openDetail(emp.overall_rank); });
            $tbody.appendChild(tr);
        });
        updateSortIndicator();
    }

    function updateSortIndicator() {
        document.querySelectorAll("#rank-table thead th.sortable").forEach(function (th) {
            th.classList.remove("sort-asc", "sort-desc");
            if (th.dataset.sort === sortField) th.classList.add(sortOrder === "asc" ? "sort-asc" : "sort-desc");
        });
    }

    function goToPage(page) {
        const totalPages = Math.max(1, Math.ceil(total / perPage));
        const p = Math.max(1, Math.min(totalPages, parseInt(page, 10) || 1));
        if (p !== currentPage) {
            currentPage = p;
            loadEmperors();
        }
    }

    function renderPagination() {
        const totalPages = Math.max(1, Math.ceil(total / perPage));
        let html = "";
        html += "<button type=\"button\" class=\"btn-page\" data-page=\"1\" " + (currentPage <= 1 ? "disabled" : "") + ">首页</button>";
        if (currentPage > 1) {
            html += "<button type=\"button\" class=\"btn-page\" data-page=\"" + (currentPage - 1) + "\">上一页</button>";
        }
        html += " <span class=\"page-info\">第 " + currentPage + " / " + totalPages + " 页，共 " + total + " 条</span> ";
        if (currentPage < totalPages) {
            html += "<button type=\"button\" class=\"btn-page\" data-page=\"" + (currentPage + 1) + "\">下一页</button>";
        }
        html += "<button type=\"button\" class=\"btn-page\" data-page=\"" + totalPages + "\" " + (currentPage >= totalPages ? "disabled" : "") + ">尾页</button>";
        html += " <span class=\"page-jump\">跳至 <input type=\"number\" id=\"page-input\" min=\"1\" max=\"" + totalPages + "\" value=\"" + currentPage + "\" aria-label=\"页码\"> 页 <button type=\"button\" id=\"btn-goto\">跳转</button></span>";
        $pagination.innerHTML = html;
        $pagination.querySelectorAll("button.btn-page").forEach(function (btn) {
            btn.addEventListener("click", function () {
                if (btn.disabled) return;
                currentPage = parseInt(btn.dataset.page, 10);
                loadEmperors();
            });
        });
        var input = document.getElementById("page-input");
        var btnGoto = document.getElementById("btn-goto");
        if (input && btnGoto) {
            input.addEventListener("keydown", function (e) {
                if (e.key === "Enter") { btnGoto.click(); }
            });
            btnGoto.addEventListener("click", function () {
                goToPage(input.value);
            });
        }
    }

    function openDetail(rank) {
        fetch(API + "/emperors/" + rank)
            .then(function (r) { return r.json(); })
            .then(function (emp) {
                if (emp.error) {
                    $detailBody.innerHTML = "<p>" + emp.error + "</p>";
                } else {
                    $detailBody.innerHTML = formatDetail(emp);
                }
                $detailModal.setAttribute("aria-hidden", "false");
                $detailModal.classList.add("open");
            })
            .catch(function () {
                $detailBody.innerHTML = "<p>加载失败</p>";
                $detailModal.setAttribute("aria-hidden", "false");
                $detailModal.classList.add("open");
            });
    }

    function formatDetail(emp) {
        const labels = {
            overall_rank: "排名",
            era: "时代",
            temple_posthumous_title: "庙/谥/称号",
            name: "姓名",
            short_comment: "短评",
            virtue: "德",
            wisdom: "智",
            fitness: "体",
            beauty: "美",
            diligence: "劳",
            ambition: "雄心",
            dignity: "尊严",
            magnanimity: "气量",
            desire_self_control: "欲望自控",
            personnel_management: "人事管理",
            national_power: "国力",
            military_diplomacy: "军事外交",
            public_support: "民心",
            economy_livelihood: "经济民生",
            historical_impact: "历史影响",
            overall_score: "综合评分"
        };
        let html = "<dl class=\"detail-dl\">";
        ["overall_rank", "era", "temple_posthumous_title", "name", "short_comment",
         "virtue", "wisdom", "fitness", "beauty", "diligence", "ambition", "dignity",
         "magnanimity", "desire_self_control", "personnel_management", "national_power",
         "military_diplomacy", "public_support", "economy_livelihood", "historical_impact", "overall_score"].forEach(function (key) {
            const val = emp[key];
            if (val === undefined || val === null) return;
            const label = labels[key] || key;
            const display = typeof val === "number" ? (key === "overall_rank" ? String(Math.round(val)) : Number(val).toFixed(1)) : (val || "-");
            html += "<dt>" + label + "</dt><dd>" + display + "</dd>";
        });
        html += "</dl>";
        return html;
    }

    function closeModal() {
        $detailModal.setAttribute("aria-hidden", "true");
        $detailModal.classList.remove("open");
    }

    $modalClose.addEventListener("click", closeModal);
    $modalBackdrop.addEventListener("click", closeModal);

    document.querySelectorAll("#rank-table thead th.sortable").forEach(function (th) {
        th.addEventListener("click", function () {
            const field = th.dataset.sort;
            if (field === sortField) {
                sortOrder = sortOrder === "asc" ? "desc" : "asc";
            } else {
                sortField = field;
                sortOrder = (field === "overall_rank" || field === "era") ? "asc" : "desc";
            }
            currentPage = 1;
            loadEmperors();
        });
    });

    $search.addEventListener("input", function () { currentPage = 1; loadEmperors(); });
    $era.addEventListener("change", function () { currentPage = 1; loadEmperors(); });
    $perPage.addEventListener("change", function () { perPage = parseInt($perPage.value, 10); currentPage = 1; loadEmperors(); });

    loadEras();
    loadEmperors();
})();
