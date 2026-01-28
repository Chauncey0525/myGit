-- 皇帝表：基于多维度评分体系的帝王评价表
-- 使用前请先创建或选择数据库: CREATE DATABASE IF NOT EXISTS your_db; USE your_db;

CREATE TABLE IF NOT EXISTS emperor_rank (
    -- primary key
    overall_rank           INT             NOT NULL PRIMARY KEY COMMENT '总排名',

    -- basic info
    era                    VARCHAR(50)     DEFAULT NULL COMMENT '时代',
    temple_posthumous_title VARCHAR(100)   DEFAULT NULL COMMENT '庙/谥/称号',
    name                   VARCHAR(50)     NOT NULL COMMENT '姓名',
    short_comment          TEXT            DEFAULT NULL COMMENT '短评',

    -- dimensions (store raw scores)
    virtue                 DECIMAL(5,2)    DEFAULT NULL COMMENT '德 (11%)',
    wisdom                 DECIMAL(5,2)    DEFAULT NULL COMMENT '智 (10%)',
    fitness                DECIMAL(5,2)    DEFAULT NULL COMMENT '体 (2%)',
    beauty                 DECIMAL(5,2)    DEFAULT NULL COMMENT '美 (2%)',
    diligence              DECIMAL(5,2)    DEFAULT NULL COMMENT '劳 (6%)',
    ambition               DECIMAL(5,2)    DEFAULT NULL COMMENT '雄心 (3%)',
    dignity                DECIMAL(5,2)    DEFAULT NULL COMMENT '尊严 (7%)',
    magnanimity            DECIMAL(5,2)    DEFAULT NULL COMMENT '气量 (4%)',
    desire_self_control    DECIMAL(5,2)    DEFAULT NULL COMMENT '欲望自控 (4%)',

    -- governance & outcomes
    personnel_management   DECIMAL(5,2)    DEFAULT NULL COMMENT '人事管理 (12%)',
    national_power         DECIMAL(5,2)    DEFAULT NULL COMMENT '国力 (6%)',
    military_diplomacy     DECIMAL(5,2)    DEFAULT NULL COMMENT '军事外交 (9%)',
    public_support         DECIMAL(5,2)    DEFAULT NULL COMMENT '民心 (7%)',
    economy_livelihood     DECIMAL(5,2)    DEFAULT NULL COMMENT '经济民生 (7%)',
    historical_impact      DECIMAL(5,2)    DEFAULT NULL COMMENT '历史影响(10%)',

    -- overall
    overall_score          DECIMAL(6,2)    DEFAULT NULL COMMENT '综合评分'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='皇帝多维度评价表';
