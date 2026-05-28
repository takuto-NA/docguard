"""Documentation style extraction and diagnostics for forbidden expressions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from docguard.constants import (
    DIAGNOSTIC_CODE_FORBIDDEN_DOCUMENTATION_EXPRESSION,
    SUGGESTION_FORBIDDEN_DOCUMENTATION_EXPRESSION,
    WHY_FORBIDDEN_DOCUMENTATION_EXPRESSION,
    YAML_FRONT_MATTER_DELIMITER,
)
from docguard.diagnostics import Diagnostic, resolve_severity_for_code
from docguard.markdown import parse_heading_line
from docguard.models import DocguardConfiguration, DocumentInspectionContext, ParsedMarkdownDocument
from docguard.prose_style import (
    GLOSSARY_TERM_LINE_PATTERN,
    build_allowed_prose_phrase_text,
    is_inside_example_dialogue_section,
    is_markdown_table_row,
    mask_markdown_syntax_for_prose_patterns,
    resolve_front_matter_end_line_index,
)

EXPECTED_RANKED_EXPRESSION_COUNT = 54


class DocumentationStyleSourceKind(str, Enum):
    HEADING = "heading"
    PROSE = "prose"
    TABLE_HEADER = "table_header"


class EnforcementStatus(str, Enum):
    ACTIVE = "active"
    SCOPED = "scoped"
    CANDIDATE = "candidate"


class DocumentationStyleViolationKind(str, Enum):
    FORBIDDEN_DOCUMENTATION_EXPRESSION = "forbidden_documentation_expression"


@dataclass(frozen=True)
class DocumentationStyleInspectionTarget:
    line_number: int
    line_text: str
    source_kind: DocumentationStyleSourceKind


@dataclass(frozen=True)
class ForbiddenDocumentationExpressionRule:
    rank: int
    label: str
    recommended_replacement: str
    source_scopes: frozenset[DocumentationStyleSourceKind]
    enforcement_status: EnforcementStatus
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class ForbiddenDocumentationExpressionMatch:
    rule: ForbiddenDocumentationExpressionRule
    line_number: int
    source_kind: DocumentationStyleSourceKind


@dataclass(frozen=True)
class DocumentationStyleCandidate:
    document_path: str
    line_number: int
    kind: DocumentationStyleViolationKind
    detail: str


HEADING_EMDASH_SUBTITLE_PATTERN = re.compile(r"\s—\s")
HEADING_PARENTHETICAL_SUBTITLE_PATTERN = re.compile(r"（[^）]+）")
HEADING_PARALLEL_SLASH_PATTERN = re.compile(r"／")
HEADING_DEKIRU_KOTO_PATTERN = re.compile(r"できること")
HEADING_KEKKYOKU_DEKIRU_PATTERN = re.compile(r"結局.*できる")
HEADING_HITOKOTO_PATTERN = re.compile(r"一言(?:で)?")
HEADING_NANI_GA_WAKATTA_PATTERN = re.compile(r"何がわかった")
HEADING_NANI_QUESTION_PATTERN = re.compile(r"^何(?:を|が)")
HEADING_YOMIKATA_PATTERN = re.compile(r"読み(?:方|順)")
HEADING_TETSUZUKI_MEMO_PATTERN = re.compile(r"手順メモ")
HEADING_SEIKA_SEIRI_PATTERN = re.compile(r"成果の整理")
HEADING_KONO_REPOSITORY_PATTERN = re.compile(r"このリポジトリ")
TABLE_HEADER_IMAE_GENZAI_PATTERN = re.compile(r"^(?:以前|現在)$")
HEADING_TROUBLESHOOT_PATTERN = re.compile(r"トラブル(?:シュート|時)")
HEADING_DEKIRU_YOUNI_PATTERN = re.compile(r"できるようになった")
HEADING_NEXT_CLI_PATTERN = re.compile(r"次に何を実行")
PROSE_MATOME_JSON_PATTERN = re.compile(r"まとめ JSON")
PROSE_KAMO_SHIMASEN_PATTERN = re.compile(r"構いません")
PROSE_TRUE_KADOUKA_PATTERN = re.compile(r"`True`かどうか")
PROSE_RESPONSIBILITY_PREFIX_PATTERN = re.compile(r"^\s*責務:\s*")
GENERAL_ZAKKURI_PATTERN = re.compile(r"ざっくり")
GENERAL_TORIAEZU_PATTERN = re.compile(r"とりあえず")
GENERAL_MAZUWA_PATTERN = re.compile(r"まずは")
GENERAL_CHOTTO_PATTERN = re.compile(r"ちょっと")
GENERAL_DAITAI_PATTERN = re.compile(r"(?:だいたい|大体)")
GENERAL_KANARI_PATTERN = re.compile(r"かなり")
GENERAL_II_KANJI_PATTERN = re.compile(r"いい感じ")
GENERAL_WAKARIYASUI_PATTERN = re.compile(r"(?:わかりやすい|分かりやすい)")
GENERAL_BENRI_PATTERN = re.compile(r"便利")
GENERAL_KANTAN_PATTERN = re.compile(r"簡単")
GENERAL_OSUSUME_PATTERN = re.compile(r"おすすめ")
GENERAL_SHITE_MIRU_PATTERN = re.compile(r"してみる")
GENERAL_SHITE_OKU_PATTERN = re.compile(r"しておく")
GENERAL_SHITE_SHIMAU_PATTERN = re.compile(r"(?:して|て)しまう")
GENERAL_TROUBLESHOOTING_PATTERN = re.compile(r"トラブルシューティング")
CHATGPT_STYLE_SUGA_YOI_PATTERN = re.compile(r"筋が(?:良|よ)い")
CHATGPT_STYLE_SHINU_PATTERN = re.compile(r"死ぬ")
CHATGPT_STYLE_STRONG_WEAK_PATTERN = re.compile(r"(?:強い|弱い)")
CHATGPT_STYLE_ITAI_PATTERN = re.compile(r"痛い")
CHATGPT_STYLE_KIKU_PATTERN = re.compile(r"効く")
CHATGPT_STYLE_CONCLUSION_PREFIX_PATTERN = re.compile(r"結論から言うと")
CHATGPT_STYLE_DESU_CONSTRUCTION_PATTERN = re.compile(
    r"(?:こうです[。.]|^\s*です[。.]|のがよいです)"
)
CHATGPT_STYLE_DEICTIC_PATTERN = re.compile(r"(?:ここ|この|それ|こう|その|あの)")
CHATGPT_STYLE_HONMEI_SEIHON_PATTERN = re.compile(r"(?:本命|正本)")
CHATGPT_STYLE_OMOI_PATTERN = re.compile(r"重い")
CHATGPT_STYLE_EXCESSIVE_ADVERB_PATTERN = re.compile(r"(?:とても|非常に|すぎる)")
CHATGPT_STYLE_CORE_WORDING_PATTERN = re.compile(r"(?:核心|中核)")


DEFAULT_FORBIDDEN_DOCUMENTATION_EXPRESSION_RULES: tuple[ForbiddenDocumentationExpressionRule, ...] = (
    ForbiddenDocumentationExpressionRule(
        rank=1,
        label="heading em dash subtitle",
        recommended_replacement="Use a noun phrase heading plus a lead sentence.",
        source_scopes=frozenset({DocumentationStyleSourceKind.HEADING}),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=HEADING_EMDASH_SUBTITLE_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=2,
        label="できること heading phrase",
        recommended_replacement="Use 機能, 機能概要, or 検証範囲.",
        source_scopes=frozenset(
            {
                DocumentationStyleSourceKind.HEADING,
                DocumentationStyleSourceKind.PROSE,
            }
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=HEADING_DEKIRU_KOTO_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=3,
        label="結局何ができるか heading phrase",
        recommended_replacement="Use 調査スコープ.",
        source_scopes=frozenset(
            {
                DocumentationStyleSourceKind.HEADING,
                DocumentationStyleSourceKind.PROSE,
            }
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=HEADING_KEKKYOKU_DEKIRU_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=4,
        label="一言 heading phrase",
        recommended_replacement="Use 概要.",
        source_scopes=frozenset(
            {
                DocumentationStyleSourceKind.HEADING,
                DocumentationStyleSourceKind.PROSE,
            }
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=HEADING_HITOKOTO_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=5,
        label="何がわかったか heading phrase",
        recommended_replacement="Use 調査結果 or 結論.",
        source_scopes=frozenset(
            {
                DocumentationStyleSourceKind.HEADING,
                DocumentationStyleSourceKind.PROSE,
            }
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=HEADING_NANI_GA_WAKATTA_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=6,
        label="heading parenthetical subtitle",
        recommended_replacement="Remove the parenthetical subtitle or move it to a lead sentence.",
        source_scopes=frozenset({DocumentationStyleSourceKind.HEADING}),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=HEADING_PARENTHETICAL_SUBTITLE_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=7,
        label="question-form heading",
        recommended_replacement="Use a noun phrase heading such as 変更内容.",
        source_scopes=frozenset({DocumentationStyleSourceKind.HEADING}),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=HEADING_NANI_QUESTION_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=8,
        label="読み方 heading phrase",
        recommended_replacement="Use ドキュメント索引 or 参照順序.",
        source_scopes=frozenset(
            {
                DocumentationStyleSourceKind.HEADING,
                DocumentationStyleSourceKind.PROSE,
            }
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=HEADING_YOMIKATA_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=9,
        label="手順メモ or 成果の整理 heading phrase",
        recommended_replacement="Use 実施手順 or ドキュメント整備成果.",
        source_scopes=frozenset(
            {
                DocumentationStyleSourceKind.HEADING,
                DocumentationStyleSourceKind.PROSE,
            }
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=re.compile(r"(?:手順メモ|成果の整理)"),
    ),
    ForbiddenDocumentationExpressionRule(
        rank=10,
        label="このリポジトリ phrase",
        recommended_replacement="Use 本リポジトリ.",
        source_scopes=frozenset(
            {
                DocumentationStyleSourceKind.HEADING,
                DocumentationStyleSourceKind.PROSE,
            }
        ),
        enforcement_status=EnforcementStatus.SCOPED,
        pattern=HEADING_KONO_REPOSITORY_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=11,
        label="table header 以前 or 現在",
        recommended_replacement="Use 変更前 and 変更後.",
        source_scopes=frozenset({DocumentationStyleSourceKind.TABLE_HEADER}),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=TABLE_HEADER_IMAE_GENZAI_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=12,
        label="トラブルシュート heading phrase",
        recommended_replacement="Use 障害切り分け.",
        source_scopes=frozenset(
            {
                DocumentationStyleSourceKind.HEADING,
                DocumentationStyleSourceKind.PROSE,
            }
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=HEADING_TROUBLESHOOT_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=13,
        label="分からない phrase",
        recommended_replacement="Use 対象外 in CLI or summary contexts.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.CANDIDATE,
        pattern=re.compile(r"分からない"),
    ),
    ForbiddenDocumentationExpressionRule(
        rank=14,
        label="できるようになった phrase",
        recommended_replacement="Use 機能概要 or 利用者・運用への効果.",
        source_scopes=frozenset(
            {
                DocumentationStyleSourceKind.HEADING,
                DocumentationStyleSourceKind.PROSE,
            }
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=HEADING_DEKIRU_YOUNI_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=15,
        label="conversational potential-form wording",
        recommended_replacement="Use neutral wording such as 抑制, 説明可能, or 参照できる.",
        source_scopes=frozenset(
            {
                DocumentationStyleSourceKind.HEADING,
                DocumentationStyleSourceKind.PROSE,
            }
        ),
        enforcement_status=EnforcementStatus.CANDIDATE,
        pattern=re.compile(r"(?:減らせる|説明できる|たどれる)"),
    ),
    ForbiddenDocumentationExpressionRule(
        rank=16,
        label="次に何を実行するか phrase",
        recommended_replacement="Use 次 CLI 選定.",
        source_scopes=frozenset(
            {
                DocumentationStyleSourceKind.HEADING,
                DocumentationStyleSourceKind.PROSE,
            }
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=HEADING_NEXT_CLI_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=17,
        label="載せられる or 読めること phrase",
        recommended_replacement="Use 利用可能 or 取得できる情報.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.CANDIDATE,
        pattern=re.compile(r"(?:載せ(?:られ|る)|読めること)"),
    ),
    ForbiddenDocumentationExpressionRule(
        rank=18,
        label="まとめ JSON phrase",
        recommended_replacement="Use 集約 JSON.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.SCOPED,
        pattern=PROSE_MATOME_JSON_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=19,
        label="構いません phrase",
        recommended_replacement="Use 省略可.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.SCOPED,
        pattern=PROSE_KAMO_SHIMASEN_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=20,
        label="Trueかどうか contract wording",
        recommended_replacement="Use 可否 or の真偽.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.SCOPED,
        pattern=PROSE_TRUE_KADOUKA_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=21,
        label="〜しやすい phrase",
        recommended_replacement="Use a neutral risk phrase such as タイムアウトリスクが高い.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.CANDIDATE,
        pattern=re.compile(r"しやすい"),
    ),
    ForbiddenDocumentationExpressionRule(
        rank=22,
        label="してよい phrase",
        recommended_replacement="Use a direct statement such as 明記する.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.CANDIDATE,
        pattern=re.compile(r"してよい"),
    ),
    ForbiddenDocumentationExpressionRule(
        rank=23,
        label="〜わけではない phrase",
        recommended_replacement="Use a direct statement such as 省略されない.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.CANDIDATE,
        pattern=re.compile(r"わけではない"),
    ),
    ForbiddenDocumentationExpressionRule(
        rank=24,
        label="table header いつ or 何を守る",
        recommended_replacement="Use 実行段階 and 検証対象.",
        source_scopes=frozenset({DocumentationStyleSourceKind.TABLE_HEADER}),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=re.compile(r"^(?:いつ|何を守る)$"),
    ),
    ForbiddenDocumentationExpressionRule(
        rank=25,
        label="very short lead sentence",
        recommended_replacement="Merge the lead into a full sentence.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.CANDIDATE,
        pattern=re.compile(r"^(?:L1|JSON のみ)。$"),
    ),
    ForbiddenDocumentationExpressionRule(
        rank=26,
        label="prose responsibility prefix",
        recommended_replacement="Integrate the responsibility statement into body prose.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=PROSE_RESPONSIBILITY_PREFIX_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=27,
        label="heading parallel slash phrasing",
        recommended_replacement="Use と or split the heading into a lead sentence.",
        source_scopes=frozenset({DocumentationStyleSourceKind.HEADING}),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=HEADING_PARALLEL_SLASH_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=28,
        label="ざっくり phrase",
        recommended_replacement="Use a precise scope or summary phrase.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_ZAKKURI_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=29,
        label="とりあえず phrase",
        recommended_replacement="State the required first action directly.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_TORIAEZU_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=30,
        label="まずは phrase",
        recommended_replacement="Use 初期手順 or a direct action label.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_MAZUWA_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=31,
        label="ちょっと phrase",
        recommended_replacement="Remove the casual degree word or use a measurable qualifier.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_CHOTTO_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=32,
        label="だいたい phrase",
        recommended_replacement="Use approximate values or explicit uncertainty.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_DAITAI_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=33,
        label="かなり phrase",
        recommended_replacement="Use a measurable qualifier or remove the vague degree word.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_KANARI_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=34,
        label="いい感じ phrase",
        recommended_replacement="Describe the concrete expected state.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_II_KANJI_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=35,
        label="わかりやすい phrase",
        recommended_replacement="Describe the readability property or remove the subjective claim.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_WAKARIYASUI_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=36,
        label="便利 phrase",
        recommended_replacement="Describe the concrete operational benefit.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_BENRI_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=37,
        label="簡単 phrase",
        recommended_replacement="Describe the actual number of steps or required operation.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_KANTAN_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=38,
        label="おすすめ phrase",
        recommended_replacement="Use 推奨 only when a normative recommendation is intended.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_OSUSUME_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=39,
        label="してみる phrase",
        recommended_replacement="Use 実行する or a direct action.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_SHITE_MIRU_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=40,
        label="しておく phrase",
        recommended_replacement="Use 準備する, 保存する, or the exact required action.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_SHITE_OKU_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=41,
        label="してしまう phrase",
        recommended_replacement="Use a direct description of the resulting state.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_SHITE_SHIMAU_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=42,
        label="トラブルシューティング phrase",
        recommended_replacement="Use 障害切り分け.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=GENERAL_TROUBLESHOOTING_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=43,
        label="筋が良い phrase",
        recommended_replacement="State the concrete reason the approach is appropriate.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=CHATGPT_STYLE_SUGA_YOI_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=44,
        label="死ぬ phrase",
        recommended_replacement="Use 停止する, 失敗する, or the exact failure mode.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=CHATGPT_STYLE_SHINU_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=45,
        label="強い or 弱い phrase",
        recommended_replacement="Use a specific property such as strict, permissive, high risk, or low risk.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=CHATGPT_STYLE_STRONG_WEAK_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=46,
        label="痛い phrase",
        recommended_replacement="Describe the concrete cost, failure, or operational impact.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=CHATGPT_STYLE_ITAI_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=47,
        label="効く phrase",
        recommended_replacement="Use 有効, 抑制する, or the exact observed effect.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=CHATGPT_STYLE_KIKU_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=48,
        label="結論から言うと phrase",
        recommended_replacement="Start with the conclusion directly without a conversational preface.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=CHATGPT_STYLE_CONCLUSION_PREFIX_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=49,
        label="abrupt です construction",
        recommended_replacement="Use a complete technical sentence or direct statement.",
        source_scopes=frozenset({DocumentationStyleSourceKind.PROSE}),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=CHATGPT_STYLE_DESU_CONSTRUCTION_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=50,
        label="deictic pronoun phrase",
        recommended_replacement="Name the concrete subject instead of using ここ, この, それ, こう, その, or あの.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=CHATGPT_STYLE_DEICTIC_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=51,
        label="本命 or 正本 phrase",
        recommended_replacement="Use 推奨案, canonical document, or the exact selected artifact.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=CHATGPT_STYLE_HONMEI_SEIHON_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=52,
        label="重い phrase",
        recommended_replacement="Use a measurable cost such as expensive, slow, or high overhead.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=CHATGPT_STYLE_OMOI_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=53,
        label="excessive adverb phrase",
        recommended_replacement="Remove the adverb or replace it with a measurable qualifier.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=CHATGPT_STYLE_EXCESSIVE_ADVERB_PATTERN,
    ),
    ForbiddenDocumentationExpressionRule(
        rank=54,
        label="核心 or 中核 phrase",
        recommended_replacement="Name the specific component, requirement, or decision.",
        source_scopes=frozenset(
            {DocumentationStyleSourceKind.HEADING, DocumentationStyleSourceKind.PROSE}
        ),
        enforcement_status=EnforcementStatus.ACTIVE,
        pattern=CHATGPT_STYLE_CORE_WORDING_PATTERN,
    ),
)


def resolve_active_forbidden_documentation_expression_rules() -> tuple[
    ForbiddenDocumentationExpressionRule,
    ...
]:
    active_rules: list[ForbiddenDocumentationExpressionRule] = []
    for rule in DEFAULT_FORBIDDEN_DOCUMENTATION_EXPRESSION_RULES:
        if rule.enforcement_status is EnforcementStatus.CANDIDATE:
            continue
        active_rules.append(rule)
    return tuple(active_rules)


def is_glossary_term_line(line_text: str) -> bool:
    return GLOSSARY_TERM_LINE_PATTERN.match(line_text.strip()) is not None


def is_markdown_table_separator_row(line_text: str) -> bool:
    stripped_line_text = line_text.strip()
    if not stripped_line_text.startswith("|"):
        return False
    separator_body = stripped_line_text.strip("|").strip()
    return re.match(
        r"^:?-{3,}:?(?:\s*\|\s*:?-{3,}:?)*\s*$",
        separator_body,
    ) is not None


def split_markdown_table_header_cells(line_text: str) -> tuple[str, ...] | None:
    stripped_line_text = line_text.strip()
    if not stripped_line_text.startswith("|"):
        return None
    if not is_markdown_table_row(line_text):
        return None
    raw_cells = stripped_line_text.strip("|").split("|")
    return tuple(cell.strip() for cell in raw_cells)


def extract_documentation_style_inspection_targets(
    parsed_document: ParsedMarkdownDocument,
) -> tuple[DocumentationStyleInspectionTarget, ...]:
    raw_lines = parsed_document.raw_text.splitlines()
    front_matter_end_line_index = resolve_front_matter_end_line_index(raw_lines)
    inspection_targets: list[DocumentationStyleInspectionTarget] = []
    inside_code_block = False

    for line_index, line_text in enumerate(raw_lines, start=1):
        if line_text.strip().startswith("```"):
            inside_code_block = not inside_code_block
            continue
        if inside_code_block:
            continue
        if front_matter_end_line_index is not None and line_index <= front_matter_end_line_index:
            continue
        if is_inside_example_dialogue_section(parsed_document.headings, line_index):
            continue

        heading = parse_heading_line(line_text, line_index)
        if heading is not None:
            inspection_targets.append(
                DocumentationStyleInspectionTarget(
                    line_number=line_index,
                    line_text=heading.text,
                    source_kind=DocumentationStyleSourceKind.HEADING,
                )
            )
            continue

        next_line_text = raw_lines[line_index] if line_index < len(raw_lines) else ""
        if is_markdown_table_row(line_text) and is_markdown_table_separator_row(next_line_text):
            table_header_cells = split_markdown_table_header_cells(line_text)
            if table_header_cells is not None:
                for table_header_cell in table_header_cells:
                    if table_header_cell == "":
                        continue
                    inspection_targets.append(
                        DocumentationStyleInspectionTarget(
                            line_number=line_index,
                            line_text=table_header_cell,
                            source_kind=DocumentationStyleSourceKind.TABLE_HEADER,
                        )
                    )
            continue

        if is_markdown_table_row(line_text):
            continue
        if is_glossary_term_line(line_text):
            continue
        if line_text.strip() == "":
            continue

        inspection_targets.append(
            DocumentationStyleInspectionTarget(
                line_number=line_index,
                line_text=line_text,
                source_kind=DocumentationStyleSourceKind.PROSE,
            )
        )

    return tuple(inspection_targets)


def compile_extra_prohibited_documentation_style_patterns(
    extra_prohibited_documentation_style_patterns: tuple[str, ...],
) -> tuple[re.Pattern[str], ...]:
    compiled_patterns: list[re.Pattern[str]] = []
    for pattern_text in extra_prohibited_documentation_style_patterns:
        compiled_patterns.append(re.compile(pattern_text, re.IGNORECASE))
    return tuple(compiled_patterns)


def build_allowed_documentation_style_phrase_text(
    line_text: str,
    allowed_documentation_style_phrases: tuple[str, ...],
) -> str:
    normalized_line_text = line_text
    for allowed_phrase in allowed_documentation_style_phrases:
        normalized_line_text = normalized_line_text.replace(allowed_phrase, "")
    return normalized_line_text


def find_forbidden_documentation_expression_matches(
    inspection_target: DocumentationStyleInspectionTarget,
    allowed_documentation_style_phrases: tuple[str, ...],
    extra_prohibited_documentation_style_patterns: tuple[re.Pattern[str], ...],
) -> tuple[ForbiddenDocumentationExpressionMatch, ...]:
    masked_line_text = mask_markdown_syntax_for_prose_patterns(inspection_target.line_text)
    masked_line_text = build_allowed_documentation_style_phrase_text(
        masked_line_text,
        allowed_documentation_style_phrases,
    )
    matched_rules: list[ForbiddenDocumentationExpressionMatch] = []

    for rule in resolve_active_forbidden_documentation_expression_rules():
        if inspection_target.source_kind not in rule.source_scopes:
            continue
        if rule.pattern.search(masked_line_text) is None:
            continue
        matched_rules.append(
            ForbiddenDocumentationExpressionMatch(
                rule=rule,
                line_number=inspection_target.line_number,
                source_kind=inspection_target.source_kind,
            )
        )

    for extra_pattern in extra_prohibited_documentation_style_patterns:
        if extra_pattern.search(masked_line_text) is None:
            continue
        matched_rules.append(
            ForbiddenDocumentationExpressionMatch(
                rule=ForbiddenDocumentationExpressionRule(
                    rank=0,
                    label=f"extra pattern {extra_pattern.pattern}",
                    recommended_replacement="Rewrite the expression in neutral documentation voice.",
                    source_scopes=frozenset(
                        {
                            DocumentationStyleSourceKind.HEADING,
                            DocumentationStyleSourceKind.PROSE,
                            DocumentationStyleSourceKind.TABLE_HEADER,
                        }
                    ),
                    enforcement_status=EnforcementStatus.ACTIVE,
                    pattern=extra_pattern,
                ),
                line_number=inspection_target.line_number,
                source_kind=inspection_target.source_kind,
            )
        )

    return tuple(matched_rules)


def format_forbidden_documentation_expression_detail(
    match: ForbiddenDocumentationExpressionMatch,
) -> str:
    rank_label = f"rank {match.rule.rank}" if match.rule.rank > 0 else "extra pattern"
    return (
        f"{rank_label}; {match.rule.label}; "
        f"{match.source_kind.value}; line {match.line_number}"
    )


def build_forbidden_documentation_expression_message(
    match: ForbiddenDocumentationExpressionMatch,
) -> str:
    rank_label = f"rank {match.rule.rank}" if match.rule.rank > 0 else "extra pattern"
    return (
        f"Forbidden documentation expression matched at line {match.line_number} "
        f"({match.source_kind.value}): {match.rule.label} ({rank_label}). "
        f"Recommended replacement: {match.rule.recommended_replacement}"
    )


def collect_documentation_style_candidates(
    configuration: DocguardConfiguration,
    document_contexts: tuple[DocumentInspectionContext, ...],
) -> tuple[DocumentationStyleCandidate, ...]:
    extra_patterns = compile_extra_prohibited_documentation_style_patterns(
        configuration.extra_prohibited_documentation_style_patterns,
    )
    candidates: list[DocumentationStyleCandidate] = []

    for inspection_context in document_contexts:
        parsed_document = inspection_context.parsed_document
        inspection_targets = extract_documentation_style_inspection_targets(parsed_document)
        for inspection_target in inspection_targets:
            matched_rules = find_forbidden_documentation_expression_matches(
                inspection_target,
                configuration.allowed_documentation_style_phrases,
                extra_patterns,
            )
            if not matched_rules:
                continue
            first_match = matched_rules[0]
            candidates.append(
                DocumentationStyleCandidate(
                    document_path=parsed_document.repository_relative_path,
                    line_number=first_match.line_number,
                    kind=DocumentationStyleViolationKind.FORBIDDEN_DOCUMENTATION_EXPRESSION,
                    detail=format_forbidden_documentation_expression_detail(first_match),
                )
            )

    return tuple(candidates)


def check_documentation_style(
    configuration: DocguardConfiguration,
    inspection_context: DocumentInspectionContext,
) -> list[Diagnostic]:
    parsed_document = inspection_context.parsed_document
    extra_patterns = compile_extra_prohibited_documentation_style_patterns(
        configuration.extra_prohibited_documentation_style_patterns,
    )
    diagnostics: list[Diagnostic] = []
    inspection_targets = extract_documentation_style_inspection_targets(parsed_document)

    for inspection_target in inspection_targets:
        matched_rules = find_forbidden_documentation_expression_matches(
            inspection_target,
            configuration.allowed_documentation_style_phrases,
            extra_patterns,
        )
        for match in matched_rules:
            diagnostics.append(
                Diagnostic(
                    code=DIAGNOSTIC_CODE_FORBIDDEN_DOCUMENTATION_EXPRESSION,
                    severity=resolve_severity_for_code(
                        DIAGNOSTIC_CODE_FORBIDDEN_DOCUMENTATION_EXPRESSION,
                        configuration.severities,
                    ),
                    document_path=parsed_document.repository_relative_path,
                    message=build_forbidden_documentation_expression_message(match),
                    why_it_matters=WHY_FORBIDDEN_DOCUMENTATION_EXPRESSION,
                    suggestion=SUGGESTION_FORBIDDEN_DOCUMENTATION_EXPRESSION,
                    location=f"line {match.line_number}",
                    document_type_name=(
                        inspection_context.document_type.name
                        if inspection_context.document_type is not None
                        else None
                    ),
                )
            )

    return diagnostics
